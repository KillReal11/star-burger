from django.db import models


class Place(models.Model):
    address = models.CharField("Адрес", unique=True, max_length=255)
    lat = models.FloatField("Широта", null=True, blank=True)
    lon = models.FloatField("Долгота", null=True, blank=True)
    requested_at = models.DateTimeField("Дата запроса", auto_now_add=True)

    class Meta:
        verbose_name = "место"
        verbose_name_plural = "места"

    def __str__(self):
        return self.address
