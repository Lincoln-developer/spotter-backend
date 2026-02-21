import pytest
from optimizer.serializers import OptimizeRouteSerializer


@pytest.mark.parametrize(
    "payload",
    [
        {
            "start_lat": 40.0,
            "start_lon": -75.0,
            "end_lat": 41.0,
            "end_lon": -76.0,
            "tank_capacity": 50,
            "mpg": 10,
            "start_fuel": 20,
        }
    ]
)
def test_serializer_valid(payload):
    serializer = OptimizeRouteSerializer(data=payload)
    assert serializer.is_valid()


def test_invalid_latitude():
    payload = {
        "start_lat": 200,
        "start_lon": -75,
        "end_lat": 41,
        "end_lon": -76,
        "tank_capacity": 50,
        "mpg": 10,
        "start_fuel": 10,
    }
    serializer = OptimizeRouteSerializer(data=payload)
    assert not serializer.is_valid()


def test_start_fuel_exceeds_capacity():
    payload = {
        "start_lat": 40,
        "start_lon": -75,
        "end_lat": 41,
        "end_lon": -76,
        "tank_capacity": 50,
        "mpg": 10,
        "start_fuel": 60,
    }
    serializer = OptimizeRouteSerializer(data=payload)
    assert not serializer.is_valid()