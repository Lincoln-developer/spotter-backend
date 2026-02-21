import polyline
from rest_framework.views import APIView
from rest_framework.response import Response

from optimizer.serializers import OptimizeRouteSerializer
from services.routing_service import get_route
from services.spatial_service import build_route_line, get_stations_along_route
from services.projection_service import compute_mile_marker
from services.optimization_service import StationDTO, optimize_fuel, RouteUnreachable

class OptimizeRouteView(APIView):

    def post(self, request):
        serializer = OptimizeRouteSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        data = serializer.validated_data

        route = get_route(
            [data["start_lon"], data["start_lat"]],
            [data["end_lon"], data["end_lat"]],
        )

        coords = polyline.decode(route["geometry"])
        route_line = build_route_line(coords)
        stations_qs = get_stations_along_route(route_line)

        station_dtos = []
        for station in stations_qs:
            mile_marker = compute_mile_marker(
                route_line,
                station.location,
                route["distance_miles"]
            )

            station_dtos.append(
                StationDTO(
                    id=station.id,
                    mile_marker=mile_marker,
                    price=station.price
                )
            )
        try:
            stops, total_cost = optimize_fuel(
                station_dtos,
                total_distance=route["distance_miles"],
                mpg=data["mpg"],
                tank_capacity=data["tank_capacity"],
                start_fuel=data["start_fuel"],
            )
        except RouteUnreachable as e:
            return Response({"error": str(e)}, status=400)
        
        return Response({
            "distance_miles": route["distance_miles"],
            "fuel_stops": stops,
            "total_cost": total_cost,
            "route_geometry": route["geometry"],
        })
