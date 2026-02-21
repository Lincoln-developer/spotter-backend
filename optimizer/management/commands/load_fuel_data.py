import os
import csv
from django.core.management.base import BaseCommand
from django.contrib.gis.geos import Point
from django.db import transaction
from optimizer.models import FuelStation
from django.conf import settings


class Command(BaseCommand):
    help = "Load fuel station data from enriched CSV file."

    def handle(self, *args, **kwargs):

        file_path = os.path.join(
            settings.BASE_DIR,
            "data",
            "fuel-prices-enriched.csv"
        )

        stations_dict = {}
        skipped = 0

        with open(file_path, newline="", encoding="utf-8") as file:
            reader = csv.DictReader(file)

            for row in reader:
                lat = row.get("Latitude")
                lon = row.get("Longitude")

                # Skip rows with missing coordinates
                if not lat or not lon:
                    skipped += 1
                    continue

                try:
                    opis_id = int(row["OPIS Truckstop ID"])

                    location = Point(
                        float(lon),
                        float(lat),
                        srid=4326
                    )

                    # Deduplicate by opis_id
                    stations_dict[opis_id] = FuelStation(
                        opis_id=opis_id,
                        name=row["Truckstop Name"],
                        city=row["City"],
                        state=row["State"],
                        price=float(row["Retail Price"]),
                        location=location,
                    )

                except (ValueError, KeyError):
                    skipped += 1
                    continue

        stations = list(stations_dict.values())

        with transaction.atomic():
            FuelStation.objects.bulk_create(
                stations,
                update_conflicts=True,
                update_fields=["name", "city", "state", "price", "location"],
                unique_fields=["opis_id"],
                batch_size=1000,
            )

        self.stdout.write(
            self.style.SUCCESS(
                f"Loaded {len(stations)} fuel stations. "
                f"Skipped {skipped} invalid rows."
            )
        )
