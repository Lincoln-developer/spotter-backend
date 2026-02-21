import pytest
from django.contrib.gis.geos import Point
from optimizer.models import FuelStation
from services.spatial_service import build_route_line, get_stations_along_route


@pytest.mark.django_db
def test_station_within_corridor():
    route = build_route_line([(40, -75), (41, -75)])

    station = FuelStation.objects.create(
        opis_id=1,
        name="Test",
        city="Test",
        state="PA",
        price=4.0,
        location=Point(-75, 40.5, srid=4326)
    )

    qs = get_stations_along_route(route)

    assert station in qs