import pytest
from fastapi import Depends
from fastapi.testclient import TestClient
import sys
from pathlib import Path
parent_dir = Path(__file__).parents[1]
sys.path.append(str(parent_dir))

from run import app
from tests.test_config import override_get_db
from routers.auth import get_current_user
from database import get_db
from models import User,Project,Skill,Request,EmployeeSkill,Project_assignment,Employee_assignment


app.dependency_overrides[get_db] = override_get_db

#to clear the db after test
def cleanup_db(db):
    db.query(EmployeeSkill).delete()

    db.query(User).filter(User.email != 'ro@gmail.com').delete()
    db.query(Project).delete()
    db.query(Skill).delete()
    db.query(Project_assignment).delete()
    db.query(Employee_assignment).delete()
    db.query(Request).delete()
    db.commit()


# Create a test client
client = TestClient(app)

def override_get_current_user_admin():
    return {"id": 1, "user_type": "admin"}
def override_get_current_user_employee():
    return {"id": 2, "user_type": "employee"}

def override_get_current_user_manager():
    return {"id": 3, "user_type": "manager"}

def override_get_current_user_not_found():
    return {"id": 999, "user_type": "employee"}


def test_login():
    formData = {
        "username": "ro@gmail.com",  
        "password": "ro12"
    }
    response = client.post("/auth/newtoken", data=formData)  
    assert response.status_code == 200
    assert "access_token" in response.json()
    assert "token_type" in response.json()
    assert "role" in response.json()


#################################################################################################################



# UPDATE PASSWORD Testing
def test_update_password_success():
    # Create a test user in the database
    db = next(override_get_db())
    test_user = User(id=2, name="Test User", email="testuser@example.com", user_type="employee", password="oldpassword")
    db.add(test_user)
    db.commit()

    app.dependency_overrides[get_current_user] = override_get_current_user_employee

    # Data for updating password
    userdata = {
        "email": "testuser@example.com",
        "password": "newpassword123"
    }

    # Make the request
    response = client.post("/update_password/", json=userdata)
    cleanup_db(db)

    # Assertions
    assert response.status_code == 200
    assert response.json() == {"message": "Password updated successfully"}



def test_update_password_user_not_found():

    db = next(override_get_db())
    test_user = User(id=2, name="Test User", email="testuser@example.com", user_type="employee", password="oldpassword")
    db.add(test_user)
    db.commit()

    app.dependency_overrides[get_current_user] = override_get_current_user_employee


    # Data for updating password
    userdata = {
        "email": "user2@example.com",
        "password": "newpassword123"
    }


    # Make the request
    response = client.post("/update_password/", json=userdata)

    cleanup_db(db)

    # Assertions
    assert response.status_code == 404
    assert response.json() == {"detail": "Email not found"}


