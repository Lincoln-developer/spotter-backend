from django.contrib.gis.db import models

class FuelStation(models.Model):
    opis_id = models.IntegerField(unique=True)
    name = models.CharField(max_length=255)
    city = models.CharField(max_length=255)
    state = models.CharField(max_length=10)
    price = models.FloatField()

    location = models.PointField(geography=True)

    def __str__(self):
        return f"{self.name} ({self.city}, {self.state})"
