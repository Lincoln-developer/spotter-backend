"""
Spatial operations for route processing.
All spatial math is performed in projected CRS (EPSG:3857).
"""

from django.contrib.gis.geos import LineString
from django.db.models import QuerySet
from optimizer.models import FuelStation

ROUTE_CRS = 4326
PROJECTED_CRS = 3857  # meters


def build_route_line(coords: list[tuple[float, float]]) -> LineString:
    """
    Build a WGS84 LineString from decoded polyline coordinates.
    coords format: [(lat, lon), ...]
    """
    return LineString(
        [(lon, lat) for lat, lon in coords],
        srid=ROUTE_CRS,
    )


def get_stations_along_route(route_line: LineString) -> QuerySet:
    """
    Returns fuel stations within 20 mile corridor around route.
    Uses projected CRS for accurate buffering.
    """

    projected_route = route_line.transform(PROJECTED_CRS, clone=True)

    corridor = projected_route.buffer(20 * 1609.34)  # 20 miles in meters
    corridor.transform(ROUTE_CRS)

    return (
        FuelStation.objects
        .filter(location__intersects=corridor)
        .only("id", "price", "location")
    )
