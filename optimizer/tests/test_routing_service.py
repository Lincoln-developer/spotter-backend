import pytest
from services.routing_service import get_route


@pytest.mark.django_db
def test_get_route_cached(mocker):

    mock_response = {
        "routes": [{
            "summary": {"distance": 1000},
            "geometry": "abc"
        }]
    }

    mock_post = mocker.patch("services.routing_service.httpx.post")

    mock_post.return_value.raise_for_status.return_value = None
    mock_post.return_value.json.return_value = mock_response

    route = get_route([-75, 40], [-76, 41])

    assert route["distance_miles"] > 0
    assert route["geometry"] == "abc"