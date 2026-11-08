import logging

import requests
from django.conf import settings
from geopy import distance

from .models import Place

logger = logging.getLogger(__name__)


def fetch_coordinates(address):
    if not address:
        return None
    response = requests.get(
        "https://geocode-maps.yandex.ru/1.x",
        params={
            "geocode": address,
            "apikey": settings.YANDEX_GEOCODER_API_KEY,
            "format": "json",
        },
        timeout=5,
    )
    response.raise_for_status()
    found = response.json()["response"]["GeoObjectCollection"]["featureMember"]
    if not found:
        return None
    lon, lat = found[0]["GeoObject"]["Point"]["pos"].split()
    return float(lat), float(lon)


def get_coordinates_by_address(addresses):
    addresses = {address for address in addresses if address}
    places = {
        place.address: place
        for place in Place.objects.filter(address__in=addresses)
    }

    new_places = []
    for address in addresses - places.keys():
        try:
            coordinates = fetch_coordinates(address)
        except (requests.exceptions.RequestException, KeyError, ValueError):
            logger.exception("Не удалось определить координаты: %s", address)
            continue
        lat, lon = coordinates or (None, None)
        new_places.append(Place(address=address, lat=lat, lon=lon))
    Place.objects.bulk_create(new_places)

    return {
        place.address: (place.lat, place.lon) if place.lat is not None else None
        for place in [*places.values(), *new_places]
    }


def get_restaurants_with_distance(order_coordinates, restaurants, coordinates):
    result = []
    for restaurant in restaurants:
        restaurant_coordinates = coordinates.get(restaurant.address)
        if order_coordinates and restaurant_coordinates:
            km = distance.distance(order_coordinates, restaurant_coordinates).km
        else:
            km = None
        result.append({"name": restaurant.name, "distance": km})
    return sorted(result, key=lambda r: (r["distance"] is None, r["distance"] or 0))
