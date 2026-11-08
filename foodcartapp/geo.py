import logging

import requests
from django.conf import settings
from geopy import distance

logger = logging.getLogger(__name__)


def fetch_coordinates(address):
    if not address:
        return None
    try:
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
    except (requests.exceptions.RequestException, KeyError, ValueError):
        logger.exception("Не удалось определить координаты: %s", address)
        return None
    if not found:
        return None
    lon, lat = found[0]["GeoObject"]["Point"]["pos"].split()
    return float(lat), float(lon)


def get_restaurants_with_distance(order_coordinates, restaurants):
    result = []
    for restaurant in restaurants:
        restaurant_coordinates = fetch_coordinates(restaurant.address)
        if order_coordinates and restaurant_coordinates:
            km = distance.distance(order_coordinates, restaurant_coordinates).km
        else:
            km = None
        result.append({"name": restaurant.name, "distance": km})
    return sorted(result, key=lambda r: (r["distance"] is None, r["distance"] or 0))