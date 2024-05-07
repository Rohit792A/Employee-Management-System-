# import pytest
from fastapi.testclient import TestClient
from app.run import app
from app.routers.employee import router as employee_router

client = TestClient(app)

def test_welcome():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "Hello World"}


def test_get_employees():
    app.include_router(employee_router)
    response = client.get("/employees")
    assert response.status_code == 200
    assert len(response.json()) > 0

def test_create_employee():
    app.include_router(employee_router)
    employee_data = {
        "name": "John Doe",
        "email": "john.doe@example.com",
        "password": "joe123",
        "user_type": "employee"
    }
    response = client.post("/employees", json=employee_data)
    assert response.status_code == 201
    assert response.json()["name"] == "John Doe"
