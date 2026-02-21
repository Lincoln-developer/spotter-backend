import httpx
import hashlib
from django.conf import settings
from django.core.cache import cache

ORS_URL = "https://api.openrouteservice.org/v2/directions/driving-car"


def get_route(start_coords, finish_coords):
    """
    Fetch route from OpenRouteService with Redis caching.
    """

    raw_key = f"{start_coords[0]}:{start_coords[1]}:{finish_coords[0]}:{finish_coords[1]}"
    cache_key = f"route:{hashlib.md5(raw_key.encode()).hexdigest()}"

    cached = cache.get(cache_key)
    if cached:
        return cached

    headers = {
        "Authorization": settings.ORS_API_KEY,
        "Content-Type": "application/json"
    }

    body = {
        "coordinates": [
            start_coords,
            finish_coords
        ]
    }

    response = httpx.post(
        ORS_URL,
        json=body,
        headers=headers,
        timeout=10
    )

    response.raise_for_status()
    data = response.json()

    route = data["routes"][0]

    result = {
        "distance_miles": route["summary"]["distance"] * 0.000621371,
        "geometry": route["geometry"]
    }

    cache.set(cache_key, result, timeout=86400)

    return result