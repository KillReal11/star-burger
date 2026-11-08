from django.contrib import admin

from .models import Place


@admin.register(Place)
class PlaceAdmin(admin.ModelAdmin):
    list_display = ("address", "lat", "lon", "requested_at")
    search_fields = ("address",)
