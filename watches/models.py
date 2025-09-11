from django.db import models

class Watch(models.Model):
    name = models.CharField(max_length=200)
    brand = models.CharField(max_length=100)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    image = models.CharField(max_length=500)
    rating = models.FloatField(default=5.0)
    features = models.JSONField(default=list)
    is_featured = models.BooleanField(default=False)
    is_exclusive = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.brand} {self.name}"
