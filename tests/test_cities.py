import json

from app import get_city_handler, list_cities_handler


def test_list_cities_returns_all_cities():
    response = list_cities_handler({}, None)

    assert response["statusCode"] == 200
    body = json.loads(response["body"])
    assert "cities" in body
    assert isinstance(body["cities"], list)
    assert len(body["cities"]) > 0


def test_get_city_returns_existing_city():
    event = {"pathParameters": {"city_id": "tokyo"}}

    response = get_city_handler(event, None)

    assert response["statusCode"] == 200
    body = json.loads(response["body"])
    assert body["city_id"] == "tokyo"


def test_get_city_returns_404_for_unknown_city():
    event = {"pathParameters": {"city_id": "unknown"}}

    response = get_city_handler(event, None)

    assert response["statusCode"] == 404
    body = json.loads(response["body"])
    assert "error" in body
