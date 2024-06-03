import pytest
from fastapi import Depends
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker,Session
from sqlalchemy.pool import StaticPool
import sys
from pathlib import Path
parent_dir = Path(__file__).parents[1]
sys.path.append(str(parent_dir))

from run import app
from tests.test_config import override_get_db
from routers.auth import get_current_user
from database import get_db,Base
from routers.employee import router as employee_router
from models import User,Project,Skill,Request,EmployeeSkill,Project_assignment,Employee_assignment

app.dependency_overrides[get_db] = override_get_db

#to clear the db after test
def cleanup_db(db):

    db.query(Project_assignment).delete()
    db.query(Request).delete()
    db.query(Project).delete()
    db.query(User).filter(User.email!='ro@gmail.com').delete()
    db.query(EmployeeSkill).delete()
    db.query(Skill).delete()
    db.query(Employee_assignment).delete()
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

##########################################################################

# REQUEST EMPLOYEES Testing

def test_request_employees_user_not_found():
    app.dependency_overrides[get_current_user] = override_get_current_user_not_found

    request_data = {
        "manager_id": 1,
        "project_id": 1,
        "requested_emp_id": 3
    }
    response = client.post("/add_new_request/", json=request_data)
    assert response.status_code == 404
    assert response.json() == {"detail": "User not found"}
    cleanup_db(next(override_get_db()))

def test_request_employees_unauthorized():
    db = next(override_get_db())
    employee = User(id=2, name="Emp", email="emp@example.com", user_type="employee", password="hashedpassword1")
    db.add(employee)
    db.commit()
    app.dependency_overrides[get_current_user] = override_get_current_user_employee
    
  
    request_data = {
        "manager_id": 3,
        "project_id": 1,
        "requested_emp_id": 11
    }
    response = client.post("/add_new_request/", json=request_data)
    assert response.status_code == 401
    assert response.json() == {"detail": "You are not authorized to perform this action"}
    cleanup_db(next(override_get_db()))

def test_request_employees_manager_not_found():

    db = next(override_get_db())
    manager = User(id  = 3,
                   name="manager", 
                   email="manager@gmail.com", 
                   password="password123", 
                   user_type="manager")
    db.add(manager)
    app.dependency_overrides[get_current_user] = override_get_current_user_manager

    #create emp and add to db
    employee1 = User(id  = 11,
                   name="employee",
                   email="emp@gmail.com",
                   password="er23",
                   user_type="employee")
    db.add(employee1)
    db.commit()

    #create 2 project and add to db
    project1 = Project(id = 1,name="project1", manager_id=3)
    db.add(project1)
    db.commit()

    request_data = {
        "manager_id": 999,
        "project_id": 1,
        "requested_emp_id": 11
    }
    response = client.post("/add_new_request/", json=request_data)
    assert response.status_code == 404
    assert response.json() == {"detail": "Manager not found"}
    cleanup_db(db)

def test_request_employees_project_not_found():
    db = next(override_get_db())
    manager = User(id=3, name="Manager", email="manager@example.com", user_type="manager", password="hashedpassword")
    db.add(manager)
    db.commit()
    app.dependency_overrides[get_current_user] = override_get_current_user_manager

     #create emp and add to db
    employee1 = User(id  = 11,
                   name="employee",
                   email="emp@gmail.com",
                   password="er23",
                   user_type="employee")
    db.add(employee1)
    db.commit()

    request_data = {
        "manager_id": 3,
        "project_id": 999,
        "requested_emp_id": 11
    }
    response = client.post("/add_new_request/", json=request_data)
    assert response.status_code == 404
    assert response.json() == {"detail": "Project not found"}
    cleanup_db(db)

def test_request_employees_manager_not_assigned():
    db = next(override_get_db())
    manager1 = User(id=3, name="Manager", email="manager@example.com", user_type="manager", password="hashedpassword")
    db.add(manager1)
    db.commit()

    app.dependency_overrides[get_current_user] = override_get_current_user_manager

    manager2 = User(id=4,name="manager2", email="manager2@gmail.com", password="password12", user_type="manager")
    db.add(manager2)

    #create emp and add to db
    employee1 = User(id  = 11,
                   name="employee",
                   email="emp@gmail.com",
                   password="er23",
                   user_type="employee")
    db.add(employee1)
    db.commit()

    #create 2 project and add to db
    project1 = Project(id = 1,name="project1", manager_id=4)
    db.add(project1)
    db.commit()

    request_data = {
        "manager_id": 3,
        "project_id": 1,
        "requested_emp_id": 11
    }
    response = client.post("/add_new_request/", json=request_data)
    assert response.status_code == 401
    assert response.json() == {"detail": "Manager is not assigned to project"}
    cleanup_db(db)

def test_request_employees_success():

    db = next(override_get_db())
    manager = User(id=3, name="Manager", email="manager@example.com", user_type="manager", password="hashedpassword")
    db.add(manager)
    db.commit()
    app.dependency_overrides[get_current_user] = override_get_current_user_manager

   
    project = Project(id=1, name="Project 1", manager_id=3)
    employee = User(id=11, name="Employee", email="employee@example.com", user_type="employee", password="hashedpassword")
    assignment = Project_assignment(project_id=1, employee_id=11)
    db.add(project)
    db.add(employee)
    db.commit()
    db.add(assignment)
    db.commit()

    request_data = {
        "manager_id": 3,
        "project_id": 1,
        "requested_emp_id": 11
    }
    response = client.post("/add_new_request/", json=request_data)
    assert response.status_code == 200

    new_request = response.json()
    assert new_request["manager_id"] == 3
    assert new_request["project_id"] == 1
    assert new_request["requested_emp_id"] == 11
    cleanup_db(db)

#############################################################################################

#GET REQUESTS Testing

def test_get_requests_user_not_found():
    app.dependency_overrides[get_current_user] = override_get_current_user_not_found

    response = client.get("/requests/")
    assert response.status_code == 404
    assert response.json() == {"detail": "User not found"}

def test_get_requests_unauthorized():
    db = next(override_get_db())
    user = User(id=2, name="Emp", email="Emp@gmail.com", user_type="employee", password="hashedpassword")
    db.add(user)
    db.commit()
    app.dependency_overrides[get_current_user] = override_get_current_user_employee

    response = client.get("/requests/")
    assert response.status_code == 401
    assert response.json() == {"detail": "You are not authorized to perform this action"}
    cleanup_db(db)

def test_get_requests_no_requests_found():
    app.dependency_overrides[get_current_user] = override_get_current_user_admin

    response = client.get("/requests/")
    assert response.status_code == 404
    assert response.json() == {"detail": "No requests found"}

def test_get_requests_success():
    app.dependency_overrides[get_current_user] = override_get_current_user_admin

    db = next(override_get_db())
    manager = User(id=3, name="Manager", email="manager@example.com", user_type="manager", password="hashedpassword")
    employee = User(id=2, name="Employee", email="employee@example.com", user_type="employee", password="hashedpassword")
    project = Project(id=1, name="Project 1", manager_id = 3)
    request1 = Request(id=1, manager_id=2, project_id=1, requested_emp_id=2)
    db.add(manager)
    db.add(employee)
    db.add(project)
    db.add(request1)
    db.commit()

    response = client.get("/requests/")
    assert response.status_code == 200
    requests = response.json()
    assert len(requests) == 1
    assert requests[0]["id"] == 1
    cleanup_db(db)



#############################################################################################

# APPROVE REQUEST Testing
def test_approve_request_unauthorized():

    db = next(override_get_db())
    user = User(id=2, name="Emp", email="Emp@gmail.com", user_type="employee", password="hashedpassword")
    db.add(user)
    db.commit()
    app.dependency_overrides[get_current_user] = override_get_current_user_employee

    response = client.put("/requests/1/approve/")
    assert response.status_code == 401
    assert response.json() == {"detail": "You are not authorized to perform this action"}
    cleanup_db(db)


def test_approve_request_user_not_found():
    app.dependency_overrides[get_current_user] = override_get_current_user_not_found

    response = client.put("/requests/1/approve/")
    assert response.status_code == 404
    assert response.json() == {"detail": "User not found"}


def test_approve_request_not_found():

    app.dependency_overrides[get_current_user] = override_get_current_user_admin
    response = client.put("/requests/999/approve/")
    assert response.status_code == 404
    assert response.json() == {"detail": "Request not found"}

def test_approve_request_success():

    db = next(override_get_db())

    manager = User(id=3, name="Manager", email="manager@example.com", user_type="manager", password="hashedpassword")
    employee = User(id=2, name="Employee", email="employee@example.com", user_type="employee", password="hashedpassword")
    project = Project(id=1, name="Project 1", manager_id=3)
    db.add(manager)
    db.add(employee)
    db.add(project)
    db.commit()
    request = Request(id=1, manager_id=3, project_id=1, requested_emp_id=2, status="pending")
    db.add(request)
    db.commit()

    response = client.put("/requests/1/approve/")
    assert response.status_code == 200
    approved_request = response.json()
    assert approved_request["id"] == 1
    assert approved_request["status"] == "approved"
    
    # Verify the employee is assigned to the project
    assignment = db.query(Project_assignment).filter_by(employee_id=2, project_id=1).first()
    assert assignment is not None

    cleanup_db(db)

################################################################################

# REJECT PROJECT Testing
def test_reject_request_already_approved():
   

    db = next(override_get_db())
    manager = User(id=3, name="Manager", email="manager@example.com", user_type="manager", password="hashedpassword")
    employee = User(id=2, name="Employee", email="employee@example.com", user_type="employee", password="hashedpassword")
    project = Project(id=1, name="Project 1", manager_id = 3)
    db.add(manager)
    db.add(employee)
    db.add(project)

    db.commit()

    request = Request(id=1, manager_id=3, project_id=1, requested_emp_id=2, status="approved")

    db.add(request)
    db.commit()

    response = client.put("/requests/1/reject/")
    assert response.status_code == 404
    assert response.json() == {"detail": "Request already approved"}
    cleanup_db(db)

def test_reject_request_success():

    db = next(override_get_db())
      
    manager = User(id=3, name="Manager", email="manager@example.com", user_type="manager", password="hashedpassword")
    employee = User(id=2, name="Employee", email="employee@example.com", user_type="employee", password="hashedpassword")
    project = Project(id=1, name="Project 1", manager_id = 3)
    db.add(manager)
    db.add(employee)
    db.add(project)

    db.commit()

    request = Request(id=1, manager_id=3, project_id=1, requested_emp_id=2, status="pending")

    db.add(request)
    db.commit()

    response = client.put("/requests/1/reject/")
    assert response.status_code == 200
    rejected_request = response.json()
    assert rejected_request["id"] == 1
    assert rejected_request["status"] == "rejected"
    cleanup_db(db)

##########################################################################

# DELETE REQUEST Testing 
def test_delete_request_unauthorized():
    db = next(override_get_db())
    user = User(id=2, name="Emp", email="Emp@gmail.com", user_type="employee", password="hashedpassword")
    db.add(user)
    db.commit()
    app.dependency_overrides[get_current_user] = override_get_current_user_employee

    response = client.delete("/requests/1")
    assert response.status_code == 401
    assert response.json() == {"detail": "You are not authorized to perform this action"}
    cleanup_db(next(override_get_db()))

def test_delete_request_not_found():
    app.dependency_overrides[get_current_user] = override_get_current_user_admin

    response = client.delete("/requests/999")
    assert response.status_code == 404
    assert response.json() == {"detail": "Request not found"}

def test_delete_request_success():
    app.dependency_overrides[get_current_user] = override_get_current_user_admin

    db = next(override_get_db())
    manager = User(id=3, name="Manager", email="manager@example.com", user_type="manager", password="hashedpassword")
    employee = User(id=2, name="Employee", email="employee@example.com", user_type="employee", password="hashedpassword")
    project = Project(id=1, name="Project 1", manager_id = 3)
    db.add(manager)
    db.add(employee)
    db.add(project)

    db.commit()

    request = Request(id=1, manager_id=3, project_id=1, requested_emp_id=2, status="pending")

    db.add(request)
    db.commit()

    response = client.delete("/requests/1")
    assert response.status_code == 200
    assert response.json() == {"message": "Request deleted successfully"}
    cleanup_db(db)