# Spotter Fuel Optimization API

A production-grade backend service that computes the cheapest possible fuel strategy along any driving route, respecting real vehicle constraints and live fuel price data.

---

## Table of Contents

- [Overview](#overview)
- [Problem Statement](#problem-statement)
- [Architecture](#architecture)
- [Key Technical Decisions](#key-technical-decisions)
- [Getting Started](#getting-started)
- [Data Pipeline](#data-pipeline)
- [Testing](#testing)

---

## Overview

The Spotter Fuel Optimization API solves a real-world logistics problem: given a long-haul driving route, where should a truck stop for fuel, and how much should it buy at each stop, to minimize total trip cost?

The system integrates real driving routes (via OpenRouteService), geospatial station filtering (via PostGIS), and a greedy optimization algorithm to return an actionable, cost-optimal fuel plan for any origin-destination pair.

**Core capabilities:**

- Real driving route computation with Redis-cached geometry
- Spatial corridor filtering to identify only reachable fuel stations
- Mile-marker projection for ordered, linear optimization
- Greedy fuel minimization with lookahead
- Bulk geospatial data ingestion from enriched CSV sources
- Fully Dockerized infrastructure — zero local dependencies required

---

## Problem Statement

**Inputs:**

| Parameter | Description |
|---|---|
| `start_lat` | Trip start latitude (address or city) |
| `start_lon` | Trip start longitude (address or city) |
| `end_lat` | Trip end latitude (address or city) |
| `end_lon` | Trip end logitude (address or city) |
| `tank_capacity` | Maximum fuel tank size (gallons) |
| `mpg` | Vehicle fuel efficiency (miles per gallon) |
| `start_fuel` | Fuel on hand at trip start (gallons) |

**The system then:**

1. Computes the real-world driving route between origin and destination.
2. Finds all fuel stations within a 20-mile corridor of that route.
3. Projects each station onto the route as a linear mile marker.
4. Runs a greedy optimization pass to determine the cheapest fueling sequence.
5. Returns a complete trip plan: route geometry, ordered stops, gallons purchased per stop, and total cost.

---

## Architecture

```
Client (Postman / Frontend)
        │
        ▼
Django REST API  (/api/optimize/)
        │
        ▼
Routing Service
  ├── OpenRouteService (driving directions)
  └── Redis Cache (md5 keyed, 24hr TTL)
        │
        ▼
Spatial Service (PostGIS)
  └── 20-mile corridor buffer in SRID 3857
        │
        ▼
Projection Service
  └── Station → mile marker mapping
        │
        ▼
Optimization Service
  └── Greedy fuel minimization algorithm
        │
        ▼
JSON Response
```

The architecture is intentionally layered. Each service has a single responsibility and can be tested, replaced, or scaled independently.

---

## Key Technical Decisions

### GeoDjango + PostGIS

All station geometry is stored as `PointField(geography=True)` in SRID 4326. Distance buffering is performed in SRID 3857 (Web Mercator) to avoid spherical distortion when computing corridor widths in meters.

`geography=True` ensures that distance calculations use the WGS84 ellipsoid rather than a flat Cartesian plane, which matters significantly over long-haul distances. Spatial indexing on the point field prevents full table scans during corridor queries.

```python
# Corridor filtering — buffer in projected CRS, query in geographic CRS
projected_route = route_line.transform(3857, clone=True)
corridor = projected_route.buffer(20 * 1609.34)  # 20 miles → meters
stations = FuelStation.objects.filter(location__intersects=corridor.transform(4326, clone=True))
```

---

### Route Corridor Filtering

Only stations within 20 miles of the route geometry are considered. This value was chosen to represent a realistic detour tolerance for long-haul trucking while keeping the candidate set computationally manageable. Scanning the full station table on every request would be prohibitively expensive and would surface irrelevant stations.

---

### Greedy Fuel Optimization

The optimization follows the canonical greedy strategy for the linear fuel problem:

- **If a cheaper station exists within reachable range** → buy only enough fuel to reach it.
- **Otherwise** → fill the tank enough to reach the next cheapest reachable opportunity, or the destination.

This strategy is provably optimal for linear routes with no backtracking: you never want to carry expensive fuel past a cheaper station, and you never want to arrive at a cheap station with a full tank purchased at a higher price.

**Time complexity:** O(n²) in the worst case due to lookahead scanning. In practice this is fast because corridor filtering limits the candidate set to a small, locally relevant subset of stations.

---

### Redis Route Caching

Route geometries from OpenRouteService are cached using:

```
key = md5(f"{origin}:{destination}")
TTL = 86400 seconds (24 hours)
```

This prevents redundant API calls for repeated or concurrent requests to the same corridor, reduces p99 latency substantially, and insulates the system from ORS rate limits during load spikes.

---

## Getting Started

### Prerequisites

- [Docker](https://docs.docker.com/get-docker/)
- [Docker Compose](https://docs.docker.com/compose/install/)

No local Python installation is required. All services run inside containers.

---

### 1. Configure Environment

Create a `.env` file in the project root:

```env
ORS_API_KEY=your_api_key_here
```

You can obtain a free API key at [openrouteservice.org](https://openrouteservice.org/dev/#/signup).

---

### 2. Start the Stack

```bash
docker-compose up --build
```

This will start:
- `spotter_db` — PostgreSQL 15 with PostGIS 3
- `spotter_redis` — Redis 7
- `spotter_web` — Django application server

---

### 3. Run Migrations

```bash
docker exec -it spotter_web python manage.py migrate
```

---

### 4. Load Fuel Station Data

```bash
docker exec -it spotter_web python manage.py load_fuel_data
```

Expected output:

```
Loaded 1878 fuel stations. Skipped 6146 invalid rows.
```

The loader deduplicates by `opis_id`, skips rows with missing coordinates, and uses `bulk_create(update_conflicts=True)` wrapped in an atomic transaction for safe re-runs.

---

## Data Pipeline

The raw fuel price dataset did not include geographic coordinates. A multi-step pipeline was built to produce an enriched, loadable dataset:

**Step 1 — Raw CSV ingestion**

The source file (`fuel-prices-for-be-assessment.csv`) contains station names, OPIS IDs, addresses, and price data — but no latitude/longitude.

**Step 2 — Batch geocoding (`batch_geocode.py`)**

The geocoding script:
- Deduplicates addresses before making API calls
- Caches results locally to avoid redundant lookups on re-runs
- Implements exponential backoff on transient failures
- Outputs `fuel-prices-enriched.csv` with resolved coordinates

**Step 3 — Bulk loading (`load_fuel_data` management command)**

The Django management command:
- Reads the enriched CSV
- Skips rows with missing or invalid coordinates
- Deduplicates on `opis_id` using `update_on_conflict`
- Executes the full import inside a single atomic transaction

---

## Testing

Run the full test suite inside the running container:

```bash
docker exec -it spotter_web pytest
```

Run tests for a specific module:

```bash
docker exec -it spotter_web pytest fuel/tests/test_serializers.py
```