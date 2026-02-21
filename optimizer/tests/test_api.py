import pytest
import polyline
from rest_framework.test import APIClient

@pytest.mark.django_db
def test_optimize_route_endpoint(mocker):

    encoded_geometry = polyline.encode([
        (40.0, -75.0),
        (41.0, -76.0),
    ])

    mocker.patch("optimizer.views.get_route").return_value = {
        "distance_miles": 100,
        "geometry": encoded_geometry,
    }

    mocker.patch("optimizer.views.get_stations_along_route").return_value = []

    client = APIClient()

    response = client.post("/api/optimize/", {
        "start_lat": 40,
        "start_lon": -75,
        "end_lat": 41,
        "end_lon": -76,
        "tank_capacity": 20,
        "mpg": 10,
        "start_fuel": 20,
    }, format="json")

    assert response.status_code == 200
    assert response.data["total_cost"] == 0