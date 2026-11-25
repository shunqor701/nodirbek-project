def test_student_registration_and_login(client):
    response = client.post("/auth/register", data={
        "full_name": "Test Talaba", "username": "student1", "email": "student1@example.com",
        "password": "Strong123!", "confirm": "Strong123!",
    })
    assert response.status_code == 302
    response = client.post("/auth/login", data={"username": "student1", "password": "Strong123!"})
    assert response.status_code == 302
    assert client.get("/student/dashboard").status_code == 200


def test_student_cannot_open_operator_area(client):
    client.post("/auth/register", data={
        "full_name": "Test Talaba", "username": "student2", "email": "student2@example.com",
        "password": "Strong123!", "confirm": "Strong123!",
    })
    client.post("/auth/login", data={"username": "student2", "password": "Strong123!"})
    assert client.get("/operator/dashboard").status_code == 403
