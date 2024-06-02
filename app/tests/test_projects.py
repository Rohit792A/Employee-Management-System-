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
from routers.employee import router as employee_router
from models import User,Project,Skill,Request,EmployeeSkill,Project_assignment,Employee_assignment


app.dependency_overrides[get_db] = override_get_db

#to clear the db after test
def cleanup_db(db):
    db.query(EmployeeSkill).delete()
    db.query(Project_assignment).delete()
    db.query(Project).delete()
    db.query(User).filter(User.email != 'ro@gmail.com').delete()
    db.query(Skill).delete()
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

###########################################################################################################


# CREATE PROJECT Testing
def test_create_projects():
    db = next(override_get_db())
    app.dependency_overrides[get_current_user] = override_get_current_user_admin
    #create manager and add to db
    manager = User(id  = 13,
                   name="manager", 
                   email="manager@gmail.com", 
                   password="password123", 
                   user_type="manager")
    db.add(manager)
    db.commit()

    test_project = {"name": "test", "manager_id": 13}
    response = client.post("/create_projects/", json=test_project)

    cleanup_db(db)
    assert response.status_code == 200    
    proj_data = response.json()
    assert isinstance(proj_data, dict)  # Since the response is expected to be a single dictionary
    
    assert "id" in proj_data
    assert "name" in proj_data
    assert "manager_id" in proj_data
    

#############################################################################################

# GET PROJECTS Testing
def test_get_projects():
    db = next(override_get_db())

    #create manager and add to db
    manager = User(id  = 3,
                   name="manager", 
                   email="manager@gmail.com", 
                   password="password123", 
                   user_type="manager")
    db.add(manager)
    db.commit()

    #create a test proj
    test_project = {"name": "test", "manager_id":3 }
    response = client.post("/create_projects/", json=test_project)
    # project_id = response.json()["id"]


    # Make a GET request to fetch all projects
    response = client.get("/projects/")
    print(response.json())
    # Assert that the response status code is 200 (OK)
    assert response.status_code == 200
    assert isinstance(response.json(), list)
    db = next(override_get_db())
    cleanup_db(db)

###########################################################################################

# GET ASSIGNED PROJECT Testing
def test_get_assigned_all():
    db = next(override_get_db())
    # create a manager in db
    manager = User(id  = 3,
                   name="manager", 
                   email="manager@gmail.com", 
                   password="password123", 
                   user_type="manager")
    db.add(manager)
    db.commit()

    #create emp and add to db
    employee1 = User(id  = 11,
                   name="employee",
                   email="emp@gmail.com",
                   password="er23",
                   user_type="employee")
    employee2 = User(id  = 12,
                   name="employee2",
                   email="emp2@gmail.com",
                   password="er22",
                   user_type="employee")
    db.add(employee1)
    db.add(employee2)
    db.commit()

    #create 2 project and add to db
    project1 = Project(id = 1,name="project1", manager_id=3)
    project2 = Project(id = 2,name="project2", manager_id=3)
    

    db.add(project1)
    db.add(project2)
    db.commit()

    
        
    # Create test project assignments
    project_assignment1 = Project_assignment(project_id=1, employee_id=11)
    project_assignment2 = Project_assignment(project_id=2, employee_id=12)
    db.add(project_assignment1)
    db.add(project_assignment2)
    db.commit()

    # Make the request
    response = client.get("/projects_assigned/")

    # Assertions
    assert response.status_code == 200
    assert len(response.json()) == 2
    assert response.json()[0]["project_id"] == 1
    assert response.json()[1]["project_id"] == 2

    # Clean up
    cleanup_db(db)

def test_get_assigned_all_unauthorized():
    db = next(override_get_db())

    # let the current user to be non-admin
    app.dependency_overrides[get_current_user] = override_get_current_user_employee

    # Make the request
    response = client.get("/projects_assigned/")

    # Assertions
    assert response.status_code == 401
    assert response.json() == {"detail": "You are not authorized to perform this action"}

    # Clean up
    cleanup_db(db)

def test_get_assigned_all_no_projects():
    db = next(override_get_db())

    app.dependency_overrides[get_current_user] = override_get_current_user_admin

    # Make the request
    response = client.get("/projects_assigned/")
    # Assertions
    assert response.status_code == 404
    assert response.json() == {"detail": "No projects found"}

    # Clean up
    cleanup_db(db)
    
#############################################################################


# ASSIGN PROJECT TO EMPLOYEE Testing

# Test for assign_employee_to_project
def test_assign_employee_to_project_unauthorized():
    app.dependency_overrides[get_current_user] = override_get_current_user_manager

    assignment_data = {"employee_id": 11, "project_id": 1}
    response = client.post("/projects/assign_employee", json=assignment_data)
    assert response.status_code == 401
    assert response.json() == {"detail": "You are not authorized to perform this action"}
    cleanup_db(next(override_get_db()))

def test_assign_employee_to_non_existent_employee():
    app.dependency_overrides[get_current_user] = override_get_current_user_admin

    # Create test project in the database
    db = next(override_get_db())
    manager = User(id  = 3,
                   name="manager", 
                   email="manager@gmail.com", 
                   password="password123", 
                   user_type="manager")
    
    project = Project(id=1, name="project1", manager_id=3)
    db.add(manager)
    db.add(project)
    db.commit()

    assignment_data = {"employee_id": 999, "project_id": 1}
    response = client.post("/projects/assign_employee", json=assignment_data)
    assert response.status_code == 404
    assert response.json() == {"detail": "Employee not found"}
    cleanup_db(db)

def test_assign_employee_to_non_existent_project():
    app.dependency_overrides[get_current_user] = override_get_current_user_admin

    # Create test employee in the database
    db = next(override_get_db())
    manager = User(id  = 3,
                name="manager",
                email="manager@gmail.com",
                password="password123",
                user_type="manager")
    db.add(manager)
    employee = User(id=11, name="employee", email="emp@gmail.com", password="er23", user_type="employee")
    db.add(employee)
    db.commit()

    assignment_data = {"employee_id": 11, "project_id": 999}
    response = client.post("/projects/assign_employee", json=assignment_data)
    assert response.status_code == 404
    assert response.json() == {"detail": "Project not found"}
    cleanup_db(db)

def test_assign_employee_already_assigned():
    app.dependency_overrides[get_current_user] = override_get_current_user_admin

    # Create test data in the database
    db = next(override_get_db())
    manager = User(id  = 3,
                name="manager",
                email="manager@gmail.com",
                password="password123",
                user_type="manager")
    employee = User(id=11, name="employee", email="emp@gmail.com", password="er23", user_type="employee")
    project = Project(id=1, name="project1", manager_id=3)
    assignment = Project_assignment( project_id=1,employee_id=11)
    db.add(employee)
    db.add(manager)
    db.add(project)
    db.commit()
    db.add(assignment)
    db.commit()

    assignment_data = {"employee_id": 11, "project_id": 1}
    response = client.post("/projects/assign_employee", json=assignment_data)
    assert response.status_code == 404
    assert response.json() == {"detail": "Employee already assigned to project"}
    cleanup_db(db)


def test_assign_employee_success():
    app.dependency_overrides[get_current_user] = override_get_current_user_admin

    # Create test data in the database
    db = next(override_get_db())
    manager = User(id  = 3,
                name="manager",
                email="manager@gmail.com",
                password="password123",
                user_type="manager")
    employee = User(id=11, name="employee", email="emp@gmail.com", password="er23", user_type="employee")
    project = Project(id=1, name="project1", manager_id=1)
    db.add(employee)
    db.add(manager)
    db.add(project)
    db.commit()

    assignment_data = {"employee_id": 11, "project_id": 1}
    response = client.post("/projects/assign_employee", json=assignment_data)
    assert response.status_code == 200
    assert response.json() == {"message": "Employee assigned to project"}
    cleanup_db(db)


#################################################################################

# UNASSIGN EMPLOYEE from Project Testing

# Test for unassign_employee_from_project
def test_unassign_employee_from_project_unauthorized():
    app.dependency_overrides[get_current_user] = override_get_current_user_employee

    employee_id = 24
    response = client.delete(f"/projects/unassign_employee/{employee_id}")
    assert response.status_code == 401
    assert response.json() == {"detail": "You are not authorized to perform this action"}
    cleanup_db(next(override_get_db()))

def test_unassign_employee_from_project_employee_not_found():
    app.dependency_overrides[get_current_user] = override_get_current_user_admin

    db = next(override_get_db())
    manager = User(id  = 3,
                name="manager",
                email="manager@gmail.com",
                password="password123",
                user_type="manager")
    db.add(manager)
    db.commit()
    project = Project(id=1, name="Project 1", manager_id=3)
    db.add(project)
    db.commit()

    employee_id = 999
    response = client.delete(f"/projects/unassign_employee/{employee_id}")
    assert response.status_code == 404
    assert response.json() == {"detail": "Employee not found"}
    cleanup_db(db)


def test_unassign_employee_from_project_not_assigned():
    app.dependency_overrides[get_current_user] = override_get_current_user_admin

    db = next(override_get_db())
   #create manager 
    manager = User(id=3, name="Manager", 
                email="manager@example.com",
                user_type="manager", 
                password="hashedpassword")

    employee = User(id=11, name="Employee", email="employee@example.com", user_type="employee", password="hashedpassword")
    project = Project(id=1, name="Project 1", manager_id=3)
    assignment = Project_assignment(project_id=1, employee_id=11)
    db.add(employee)
    db.add(project)
    db.add(manager)
    db.commit()

    employee_id  = 11   
    response = client.delete(f"/projects/unassign_employee/{employee_id}")
    assert response.status_code == 404
    assert response.json() == {"detail": "Employee not assigned to any project"}
    cleanup_db(db)

def test_unassign_employee_from_project_success():
    app.dependency_overrides[get_current_user] = override_get_current_user_admin

    db = next(override_get_db())
    #create manager 
    manager = User(id=3, name="Manager", 
                email="manager@example.com",
                user_type="manager", 
                password="hashedpassword")
    employee = User(id=11, name="Employee", email="employee@example.com", user_type="employee", password="hashedpassword")
    project = Project(id=1, name="Project 1", manager_id=3)
    assignment = Project_assignment(project_id=1, employee_id=11)
    db.add(employee)
    db.add(project)
    db.add(manager)
    db.commit()
    db.add(assignment)
    db.commit()

    employee_id = 11
    response = client.delete(f"/projects/unassign_employee/{employee_id}")
    assert response.status_code == 200
    assert response.json() == {"message": "Employee unassigned from project"}
    cleanup_db(db)


