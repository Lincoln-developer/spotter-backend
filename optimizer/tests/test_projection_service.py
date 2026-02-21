from django.contrib.gis.geos import LineString, Point
from services.projection_service import compute_mile_marker


def test_projection_midpoint():
    route = LineString(
        [(-75, 40), (-75, 41)],
        srid=4326,
    )

    station = Point(-75, 40.5, srid=4326)

    mile = compute_mile_marker(route, station, total_miles=100)

    assert 45 <= mile <= 55