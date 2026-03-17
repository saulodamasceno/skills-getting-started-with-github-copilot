from copy import deepcopy

import pytest
from fastapi.testclient import TestClient

from app import app, activities

client = TestClient(app)


@pytest.fixture(autouse=True)
def reset_activities() -> None:
    """Reset in-memory activities between tests to avoid state leakage."""

    original = deepcopy(activities)
    yield
    activities.clear()
    activities.update(original)


def test_root_redirects_to_static_index():
    # Arrange
    # (no setup needed beyond app import)

    # Act
    response = client.get("/", follow_redirects=False)

    # Assert
    assert response.status_code == 307
    assert response.headers["location"] == "/static/index.html"


def test_get_activities_returns_expected_structure():
    # Arrange

    # Act
    response = client.get("/activities")

    # Assert
    assert response.status_code == 200
    json_body = response.json()
    assert isinstance(json_body, dict)
    assert "Chess Club" in json_body
    assert "description" in json_body["Chess Club"]
    assert "participants" in json_body["Chess Club"]


def test_signup_then_duplicate_signup_errors():
    # Arrange
    email = "test@student.edu"
    activity_name = "Chess Club"

    # Act
    signup_response = client.post(f"/activities/{activity_name}/signup", params={"email": email})

    # Assert
    assert signup_response.status_code == 200
    assert signup_response.json()["message"] == f"Signed up {email} for {activity_name}"

    # Act (duplicate signup)
    duplicate_response = client.post(
        f"/activities/{activity_name}/signup", params={"email": email}
    )

    # Assert
    assert duplicate_response.status_code == 400
    assert "already signed up" in duplicate_response.json()["detail"].lower()


def test_signup_fails_for_unknown_activity():
    # Arrange
    email = "test@student.edu"
    activity_name = "Nonexistent Club"

    # Act
    response = client.post(f"/activities/{activity_name}/signup", params={"email": email})

    # Assert
    assert response.status_code == 404
    assert response.json()["detail"] == "Activity not found"


def test_unregister_then_cannot_unregister_again():
    # Arrange
    email = "test@student.edu"
    activity_name = "Chess Club"

    # Make sure the user is signed up first
    signup_response = client.post(f"/activities/{activity_name}/signup", params={"email": email})
    assert signup_response.status_code == 200

    # Act
    unregister_response = client.delete(
        f"/activities/{activity_name}/unregister", params={"email": email}
    )

    # Assert
    assert unregister_response.status_code == 200
    assert unregister_response.json()["message"] == f"Unregistered {email} from {activity_name}"

    # Act (unregister again)
    second_response = client.delete(
        f"/activities/{activity_name}/unregister", params={"email": email}
    )

    # Assert
    assert second_response.status_code == 400
    assert "not signed up" in second_response.json()["detail"].lower()


def test_unregister_fails_for_unknown_activity():
    # Arrange
    email = "test@student.edu"
    activity_name = "Unknown Club"

    # Act
    response = client.delete(
        f"/activities/{activity_name}/unregister", params={"email": email}
    )

    # Assert
    assert response.status_code == 404
    assert response.json()["detail"] == "Activity not found"
