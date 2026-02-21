"""
Greedy fuel optimization algorithm.
"""

from dataclasses import dataclass
from typing import List, Tuple


@dataclass(slots=True)
class StationDTO:
    id: int | None
    mile_marker: float
    price: float


class RouteUnreachable(Exception):
    pass


def optimize_fuel(
    stations: List[StationDTO],
    total_distance: float,
    mpg: float,
    tank_capacity: float,
    start_fuel: float,
) -> Tuple[List[dict], float]:

    max_range = tank_capacity * mpg
    current_fuel = start_fuel
    current_position = 0.0
    total_cost = 0.0
    stops = []

    stations = sorted(stations, key=lambda s: s.mile_marker)

    # Append destination marker
    stations.append(
        StationDTO(id=None, mile_marker=total_distance, price=None)
    )

    for i, station in enumerate(stations):

        distance = station.mile_marker - current_position

        if distance > max_range:
            raise RouteUnreachable("Segment exceeds max vehicle range.")

        fuel_needed_to_reach_station = distance / mpg

        if current_fuel < fuel_needed_to_reach_station:
            raise RouteUnreachable("Not enough fuel to reach next station.")

        # Consume fuel to reach this station
        current_fuel -= fuel_needed_to_reach_station
        current_position = station.mile_marker

        # If destination → stop
        if station.id is None:
            break

        # Calculate remaining trip requirement
        remaining_distance = total_distance - station.mile_marker
        fuel_needed_to_finish = remaining_distance / mpg

        # Look ahead for cheaper station reachable from HERE
        cheaper_station = None
        for future in stations[i + 1:]:
            if future.id is None:
                break
            if (
                future.price < station.price and
                future.mile_marker - station.mile_marker <= max_range
            ):
                cheaper_station = future
                break

        if cheaper_station:
            # Buy just enough to reach cheaper station
            distance_to_cheaper = cheaper_station.mile_marker - station.mile_marker
            fuel_needed = distance_to_cheaper / mpg

            fuel_to_buy = max(0.0, fuel_needed - current_fuel)

        else:
            # Fill — BUT cap by finish requirement
            max_fill_allowed = min(
                tank_capacity - current_fuel,
                fuel_needed_to_finish - current_fuel
            )

            fuel_to_buy = max(0.0, max_fill_allowed)

        cost = fuel_to_buy * station.price
        total_cost += cost

        if fuel_to_buy > 1e-6:
            stops.append({
                "station_id": station.id,
                "mile_marker": round(station.mile_marker, 2),
                "price": station.price,
                "gallons": round(fuel_to_buy, 2),
                "cost": round(cost, 2),
            })

        current_fuel += fuel_to_buy

    return stops, round(total_cost, 2)
