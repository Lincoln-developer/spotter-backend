"""
Batch geocoding script for fuel station dataset.

This is a ONE-TIME data enrichment step.

Features:
- Aggressive local JSON caching
- Address deduplication
- Rate-limit handling (1 req/sec for Nominatim)
- Exponential backoff retries
- Idempotent (safe to re-run)
"""

import csv
import json
import time
import httpx
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent.parent

INPUT_FILE = BASE_DIR / "data" / "fuel-prices-for-be-assessment.csv"
OUTPUT_FILE = BASE_DIR / "data" / "fuel-prices-enriched.csv"
CACHE_FILE = BASE_DIR / "data" / "geocode_cache.json"

NOMINATIM_URL = "https://nominatim.openstreetmap.org/search"

RATE_LIMIT_DELAY = 1.1  # seconds (Nominatim requires 1/sec)
MAX_RETRIES = 5


def normalize_address(address, city, state):
    return (
        f"{address.strip().lower()}, "
        f"{city.strip().lower()}, "
        f"{state.strip().lower()}, usa"
    )


def load_cache():
    if CACHE_FILE.exists():
        return json.loads(CACHE_FILE.read_text())
    return {}


def save_cache(cache):
    CACHE_FILE.write_text(json.dumps(cache, indent=2))


def geocode(client, query):
    """
    Geocode with retry and exponential backoff.
    """
    for attempt in range(MAX_RETRIES):
        try:
            response = client.get(
                NOMINATIM_URL,
                params={
                    "q": query,
                    "format": "json",
                    "limit": 1,
                },
                headers={
                    "User-Agent": "spotter-batch-geocoder/1.0"
                },
                timeout=10,
            )

            response.raise_for_status()
            data = response.json()

            if not data:
                return None

            return {
                "lat": float(data[0]["lat"]),
                "lon": float(data[0]["lon"]),
            }

        except Exception as e:
            wait = 2 ** attempt
            print(f"Retry {attempt+1}/{MAX_RETRIES} for {query} (wait {wait}s)")
            time.sleep(wait)

    print(f"FAILED to geocode: {query}")
    return None


# -----------------------------
# Main Pipeline
# -----------------------------

def main():

    print("Loading cache...")
    cache = load_cache()

    print("Reading CSV...")
    with INPUT_FILE.open() as f:
        rows = list(csv.DictReader(f))

    # Deduplicate addresses
    unique_queries = {}
    for row in rows:
        query = normalize_address(
            row["Address"],
            row["City"],
            row["State"],
        )
        unique_queries[query] = None

    print(f"Total rows: {len(rows)}")
    print(f"Unique addresses: {len(unique_queries)}")

    with httpx.Client() as client:

        for i, query in enumerate(unique_queries.keys(), start=1):

            if query in cache:
                continue

            print(f"[{i}/{len(unique_queries)}] Geocoding: {query}")

            result = geocode(client, query)

            if result:
                cache[query] = result
            else:
                cache[query] = None

            save_cache(cache)

            time.sleep(RATE_LIMIT_DELAY)

    # Enrich rows
    enriched_rows = []

    for row in rows:
        query = normalize_address(
            row["Address"],
            row["City"],
            row["State"],
        )

        coords = cache.get(query)

        if coords:
            row["Latitude"] = coords["lat"]
            row["Longitude"] = coords["lon"]
        else:
            row["Latitude"] = ""
            row["Longitude"] = ""

        enriched_rows.append(row)

    print("Writing enriched CSV...")
    fieldnames = list(rows[0].keys()) + ["Latitude", "Longitude"]

    with OUTPUT_FILE.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(enriched_rows)

    print("Done.")
    print("Geocoding complete. You can now disable geocoding in production.")


if __name__ == "__main__":
    main()