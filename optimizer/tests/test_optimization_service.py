import pytest
from services.optimization_service import optimize_fuel, StationDTO, RouteUnreachable


def test_no_stops_needed():
    stops, cost = optimize_fuel(
        stations=[],
        total_distance=100,
        mpg=10,
        tank_capacity=20,
        start_fuel=20,
    )
    assert stops == []
    assert cost == 0


def test_simple_two_station_case():
    stations = [
        StationDTO(id=1, mile_marker=50, price=4.0),
        StationDTO(id=2, mile_marker=80, price=3.0),
    ]

    stops, cost = optimize_fuel(
        stations=stations,
        total_distance=100,
        mpg=10,
        tank_capacity=10,
        start_fuel=5,
    )

    assert len(stops) >= 1
    assert cost >= 0


def test_unreachable_segment():
    stations = [
        StationDTO(id=1, mile_marker=300, price=4.0),
    ]

    with pytest.raises(RouteUnreachable):
        optimize_fuel(
            stations=stations,
            total_distance=300,
            mpg=10,
            tank_capacity=10,
            start_fuel=10,
        )