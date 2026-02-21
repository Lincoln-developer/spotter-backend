"""
Projection utilities for computing mile markers.
"""

PROJECTED_CRS = 3857


def compute_mile_marker(route_line, station_point, total_miles):
    """
    Compute station mile marker along route using projected CRS.
    """

    projected_route = route_line.transform(PROJECTED_CRS, clone=True)
    projected_station = station_point.transform(PROJECTED_CRS, clone=True)

    projection_distance = projected_route.project(projected_station)
    total_length = projected_route.length

    fraction = projection_distance / total_length
    return fraction * total_miles
