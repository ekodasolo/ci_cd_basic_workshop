import json

from data import CITIES


def list_cities_handler(event, context):
    return _response(200, {"cities": list(CITIES.values())})


def get_city_handler(event, context):
    city_id = event["pathParameters"]["city_id"]
    city = CITIES.get(city_id)
    if city is None:
        return _response(404, {"error": "City not found", "city_id": city_id})
    return _response(200, city)


def _response(status, body):
    return {
        "statusCode": status,
        "headers": {"Content-Type": "application/json; charset=utf-8"},
        "body": json.dumps(body, ensure_ascii=False),
    }
