import pytest
from django.core.management import call_command
from optimizer.models import FuelStation


@pytest.mark.django_db
def test_load_fuel_data(tmp_path, settings):

    data_dir = tmp_path / "data"
    data_dir.mkdir()

    file = data_dir / "fuel-prices-enriched.csv"

    file.write_text(
        "OPIS Truckstop ID,Truckstop Name,City,State,Retail Price,Latitude,Longitude\n"
        "1,Test Station,City,PA,4.0,40.0,-75.0\n"
    )

    settings.BASE_DIR = tmp_path

    call_command("load_fuel_data")

    assert FuelStation.objects.count() == 1