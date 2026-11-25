def test_student_can_register_login_and_load_orders(client):
    response = client.post(
        "/api/auth/register",
        json={
            "fullName": "Test Talaba",
            "username": "api_student",
            "email": "api_student@example.com",
            "password": "Strong123!",
            "confirm": "Strong123!",
        },
    )
    assert response.status_code == 201
    assert response.json["user"]["role"] == "student"

    response = client.post(
        "/api/auth/login",
        json={"username": "api_student", "password": "Strong123!"},
    )
    assert response.status_code == 200

    response = client.get("/api/student/orders")
    assert response.status_code == 200
    assert response.json["orders"] == []


def test_student_api_requires_authentication(client):
    response = client.get("/api/student/orders")
    assert response.status_code == 401
    assert response.is_json
