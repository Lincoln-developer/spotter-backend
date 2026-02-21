from rest_framework import serializers


class OptimizeRouteSerializer(serializers.Serializer):
    start_lat = serializers.FloatField()
    start_lon = serializers.FloatField()
    end_lat = serializers.FloatField()
    end_lon = serializers.FloatField()

    tank_capacity = serializers.FloatField(min_value=0)
    mpg = serializers.FloatField(min_value=0)
    start_fuel = serializers.FloatField(min_value=0)

    def validate(self, data):
        for field in ["start_lat", "end_lat"]:
            if not -90 <= data[field] <= 90:
                raise serializers.ValidationError("Invalid latitude.")

        for field in ["start_lon", "end_lon"]:
            if not -180 <= data[field] <= 180:
                raise serializers.ValidationError("Invalid longitude.")
        
        if data["start_fuel"] > data["tank_capacity"]:
            raise serializers.ValidationError(
                "start_fuel cannot exceed tank_capacity."
            )

        return data
