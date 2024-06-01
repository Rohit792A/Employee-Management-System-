
import pytest
from fastapi import Depends
from fastapi.testclient import TestClient
import sys
from pathlib import Path
parent_dir = Path(__file__).parents[1]
sys.path.append(str(parent_dir))

from run import app
from configtest import override_get_db
from routers.auth import get_current_user
from database import get_db
from routers.employee import router as employee_router
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



#############################################################################################################

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

#############################################################################################################


def test_create_emp():
    db = next(override_get_db())
    # Assuming a logged-in user with admin privileges
    user_data = {
         "name": "Joe",
        "email": "joe@gmail.com",
  "user_type": "employee",
  "password": "joe12"
    }
    
    response = client.post("/Create-employees/", json=user_data)
    
    assert response.status_code == 200
    
    emp_data = response.json()
    assert isinstance(emp_data, dict)  # Since the response is expected to be a single dictionary
    
    assert "id" in emp_data
    assert "name" in emp_data
    assert "email" in emp_data
    assert "user_type" in emp_data
    cleanup_db(db)

#############################################################################################################

def test_get_employees():

    # Make a GET request to fetch all employees
    response = client.get("/employees/")
    print(response.json())
    # Assert that the response status code is 200 (OK)
    assert response.status_code == 200
    assert isinstance(response.json(), list)
    db = next(override_get_db())
    cleanup_db(db)
    

#############################################################################################################

# Test the delete_employee function
def test_delete_employee():

    # Create a test employee
    test_employee = {"name": "Joe", "email": "j@example.com", "user_type": "employee", "password": "pa123"}
    response = client.post("/Create-employees/", json=test_employee)
    employee_id = response.json()["id"]

    # Test deleting the employee authorized and existent employee
    response = client.delete(f"/employees/{employee_id}")
    assert response.status_code == 200
    assert response.json() == {"message": "Employee deleted successfully"}

    # Test deleting a non-existent employee
    response = client.delete("/employees/999")
    assert response.status_code == 404
    assert response.json() == {"detail": "Employee not found"}

    # Test deleting an employee as a non-admin user

    app.dependency_overrides[get_current_user] = override_get_current_user_employee
    employee_id = 2
    
    response = client.delete(f"/employees/{employee_id}")
    assert response.status_code == 401
    assert response.json() == {"detail": "Unauthorized"}

#############################################################################################################


#EMP DETAILS TESTING
def test_user_not_found():
    app.dependency_overrides[get_current_user] = override_get_current_user_not_found
    response = client.get("/employeedetails/99")
    assert response.status_code == 404
    assert response.json() == {"detail": "User not found"}

def test_unauthorized_employee_access():

    # Create a test employee in the database
    db = next(override_get_db())
    test_employee = User(id=12, name="test1", email="t12@example.com", user_type="employee", password="pa1")
    employee = User(id=2, name="Employee", email="employee@example.com", user_type="employee", password="hashedpassword")

    db.add(test_employee)
    db.add(employee)
    db.commit()
    app.dependency_overrides[get_current_user] = override_get_current_user_employee

    response = client.get(f"/employeedetails/12")
    assert response.status_code == 401
    assert response.json() == {"detail": "Unauthorized"}
    cleanup_db(db)

def test_unauthorized_manager_access():
    app.dependency_overrides[get_current_user] = override_get_current_user_manager
    db = next(override_get_db())
    # Ensure the manager does not manage employee with id 2
    employee = User(id=3, name="Manager", email="manager@example.com", user_type="manager", password="hashedpassword1")
    db.add(employee)
    db.commit()

    response = client.get("/employeedetails/2")
    assert response.status_code == 401
    assert response.json() == {"detail": "Unauthorized"}
    cleanup_db(db)

def test_employee_view_own_details():
    app.dependency_overrides[get_current_user] = override_get_current_user_employee

    # Create a test employee in the database
    db = next(override_get_db())
    employee = User(id=2, name="Employee", email="employee@example.com", user_type="employee", password="hashedpassword")
    db.add(employee)
    db.commit()

    response = client.get("/employeedetails/2")
    assert response.status_code == 200
    assert "id" in response.json()
    assert response.json()["id"] == 2
    cleanup_db(db)

def test_manager_view_own_and_employee_details():
    app.dependency_overrides[get_current_user] = override_get_current_user_manager
    
    # Create a test manager and an employee in the database
    db = next(override_get_db())
    test_manager = User(id=3, name="Manager", email="manager@example.com", user_type="manager", password="hashedpassword")
    test_employee = User(id=2, name="Employee", email="employee@example.com", user_type="employee", password="hashedpassword")
    db.add(test_manager)
    db.add(test_employee)
    db.commit()

    response = client.get("/employeedetails/3")
    assert response.status_code == 200
    # Validate the response structure and data as per your model
    assert "id" in response.json()
    assert response.json()["id"] == 3

    # Ensure manager can view own details
    response = client.get("/employeedetails/2")
    assert response.status_code == 200
    assert "id" in response.json()
    assert response.json()["id"] == 2
    assert response.json()["name"] == "Employee"
    assert response.json()["email"] == "employee@example.com"
    assert response.json()["user_type"] == "employee"

    #clear db
    cleanup_db(db)
    

#############################################################################################################


#UPDATE testing

def test_update_employee_unauthorized():
    app.dependency_overrides[get_current_user] = override_get_current_user_employee

    # Create a test employee in the database
    db = next(override_get_db())
    test_employee = User(id=2, name="Joe", email="joe@example.com", user_type="employee", password="hashedpassword")
    db.add(test_employee)

    update_data = {"name": "Joe Updated", "email": "joe_updated@example.com", "password": "newpassword", "user_type": "employee"}
    response = client.put(f"/employees/2", json=update_data)
    assert response.status_code == 401
    assert response.json() == {"detail": "Unauthorized"}
    cleanup_db(db)

def test_update_non_existent_employee():
    app.dependency_overrides[get_current_user] = override_get_current_user_admin

    update_data = {"name": "Non Existent", "email": "nonexistent@example.com", "password": "password", "user_type": "employee"}
    response = client.put(f"/employees/999", json=update_data)
    assert response.status_code == 404
    assert response.json() == {"detail": "Employee not found"}

def test_update_employee_authorized():
    app.dependency_overrides[get_current_user] = override_get_current_user_admin

    # Create a test employee in the database
    db = next(override_get_db())
    test_employee = User(id=2, name="Joe", email="joe@example.com", user_type="employee", password="hashedpassword")
    db.add(test_employee)

    update_data = {"name": "Joe Updated", "email": "joe_updated@example.com", "password": "newpassword", "user_type": "employee"}
    response = client.put(f"/employees/2", json=update_data)
    assert response.status_code == 200
    updated_employee = response.json()
    assert updated_employee["name"] == "Joe Updated"
    assert updated_employee["email"] == "joe_updated@example.com"
    assert updated_employee["user_type"] == "employee"
    cleanup_db(db)

def test_update_employee_data_validation():
    app.dependency_overrides[get_current_user] = override_get_current_user_admin

    # Create a test employee in the database
    db = next(override_get_db())
    test_employee = User(id=11, name="James", email="ja@example.com", user_type="employee", password="hashedpassword")
    db.add(test_employee)
    db.commit()

    update_data = {"name": "", "email": "invalidemail", "password": "short", "user_type": "unknown"}
    response = client.put(f"/employees/2", json=update_data)
    assert response.status_code == 422  # As validation error returns 422 status
    cleanup_db(db)

#############################################################################################################

# Test for create_skill
def test_create_skill_unauthorized():

    # Create a test employee in the database
    db = next(override_get_db())
    test_employee = User(id=14, name="Joe", email="j@example.com", user_type="employee", password="hashedpassword")
    db.add(test_employee)
    db.commit()
    app.dependency_overrides[get_current_user] = override_get_current_user_employee

    skill_data = {"name": "Java"}
    response = client.post("/new_skills", json=skill_data)
    assert response.status_code == 401
    assert response.json() == {"detail": "Unauthorized"}
    cleanup_db(db)

def test_create_skill_success():
    app.dependency_overrides[get_current_user] = override_get_current_user_admin


    skill_data = {"name": "Python"}
    response = client.post("/new_skills", json=skill_data)
    assert response.status_code == 200
    created_skill = response.json()
    assert created_skill == {"message": "Skill added successfully"}

def test_create_skill_already_exists():
    app.dependency_overrides[get_current_user] = override_get_current_user_admin

    db = next(override_get_db())
    skill = Skill(name="Python")
    db.add(skill)
    db.commit()

    skill_data = {"name": "Python"}
    response = client.post("/new_skills", json=skill_data)
    assert response.status_code == 400
    assert response.json() == {"detail": "Skill already exists"}
    cleanup_db(db)

# Test for delete_skill
def test_delete_skill_unauthorized():
    # Create a test employee in the database
    db = next(override_get_db())
    test_employee = User(id=14, name="Joe", email="j@example.com", user_type="employee", password="hashedpassword")
    db.add(test_employee)
    db.commit()
    app.dependency_overrides[get_current_user] = override_get_current_user_employee

    response = client.delete("/skills/1")
    assert response.status_code == 401
    assert response.json() == {"detail": "Unauthorized"}
    cleanup_db(next(override_get_db()))

def test_delete_skill_not_found():
    app.dependency_overrides[get_current_user] = override_get_current_user_admin

    response = client.delete("/skills/999")
    assert response.status_code == 404
    assert response.json() == {"detail": "Skill not found"}

############################################################################################


#ADD SKILLS TEsing

def test_add_employee_skills_employee_success():

    # Create a test employee in the database
    db = next(override_get_db())

     # Create test skills
    skill1 = Skill(id=1, name="Python")
    skill2 = Skill(id=2, name="FastAPI")
    db.add(skill1)
    db.add(skill2)
    db.commit()
    test_employee_id = 2  # Assuming the current user is employee with ID 2
    test_employee = User(id=test_employee_id, name="Test Employee", email="e1@example.com", user_type="employee", password="hashedpassword")
    db.add(test_employee)
    db.commit()


    # Mock current user as an employee trying to update their own skills
    app.dependency_overrides[get_current_user] = override_get_current_user_employee


    # Mock the request data
    employee_skill_update_data = {"skill_ids": [1, 2]}  # Assuming skill IDs to add

    # Make the request
    response = client.post(f"/employees/{test_employee_id}/addskills/", json=employee_skill_update_data)

    # Assertions
    assert response.status_code == 200
    assert response.json() == {"message": "Employee skills updated successfully"}

    # Clean up
    cleanup_db(db)


# Test for unauthorized access attempt by an employee trying to update other employee's skills
def test_add_employee_skills_employee_unauthorized():

    db = next(override_get_db())
    # Create a test employee in the database
    test_employee_id = 2  # Assuming the current user is employee with ID 2
    test_employee = User(id=test_employee_id, name="Test Employee", email="e1@example.com", user_type="employee", password="hashedpassword")
    db.add(test_employee)
    db.commit()
    app.dependency_overrides[get_current_user] = override_get_current_user_employee

    # Assuming the current user is employee with ID 1
    current_employee_id = 1
    target_employee_id = 4  # ID of the employee to update
      # Create test skills
    skill1 = Skill(id=1, name="Python")
    skill2 = Skill(id=2, name="FastAPI")
    db.add(skill1)
    db.add(skill2)
    db.commit()
    # Mock the request data
    employee_skill_update_data = {"skill_ids": [1, 2]}  # Assuming skill IDs to add

    # Make the request
    response = client.post(f"/employees/{target_employee_id}/addskills/", json=employee_skill_update_data)
    cleanup_db(db)

    # Assertions
    assert response.status_code == 401
    assert response.json() == {"detail": "Unauthorized"}

# Test for non-existing employee ID
def test_add_employee_skills_employee_not_found():
    app.dependency_overrides[get_current_user] = override_get_current_user_employee

    # Assuming the current user is employee with ID 999
    target_employee_id = 999  # Non-existing employee ID

    # Mock the request data
    employee_skill_update_data = {"skill_ids": [1, 2]}  # Assuming skill IDs to add

    # Make the request
    response = client.post(f"/employees/{target_employee_id}/addskills/", json=employee_skill_update_data)

    # Assertions
    assert response.status_code == 404
    assert response.json() == {"detail": "User not found"}

#############################################################################################################

def test_get_all_skills_success():
    app.dependency_overrides[get_current_user] = override_get_current_user_admin  # Assuming this is an authorized user

    # Create a test user and skills in the database
    db = next(override_get_db())
    skill1 = Skill(id=1, name="Python")
    skill2 = Skill(id=2, name="FastAPI")
    db.add(skill1)
    db.add(skill2)
    db.commit()

    response = client.get("/skills/")
    assert response.status_code == 200
    skills = response.json()
    assert len(skills) == 2
    assert skills[0]["name"] == "Python"
    assert skills[1]["name"] == "FastAPI"

    # Clean up
    cleanup_db(db)

def test_get_all_skills_user_not_found():
    app.dependency_overrides[get_current_user] = override_get_current_user_not_found  # Assuming this user does not exist

    response = client.get("/skills/")
    assert response.status_code == 404
    assert response.json() == {"detail": "User not found"}

def test_get_all_skills_no_skills_found():
    app.dependency_overrides[get_current_user] = override_get_current_user_admin  # Assuming this is an authorized user

    # Create a test user in the database
    db = next(override_get_db())
    response = client.get("/skills/")
    assert response.status_code == 404
    assert response.json() == {"detail": "No skill found"}

    # Clean up
    cleanup_db(db)


# #############################################################################################################

#UPDATE SKILLS Testing

def test_update_employee_skills_employee_success():

    # Create a test employee in the database
    db = next(override_get_db())

     # Create test skills
    skill1 = Skill(id=1, name="Python")
    skill2 = Skill(id=2, name="FastAPI")
    db.add(skill1)
    db.add(skill2)
    db.commit()
    test_employee_id = 2  # Assuming the current user is employee with ID 2
    test_employee = User(id=test_employee_id, name="Test Employee", email="e1@example.com", user_type="employee", password="hashedpassword")
    #update employee_skill
    employee_skill = EmployeeSkill(employee_id=test_employee_id, skill_id=1)
    db.add(employee_skill)
    db.add(test_employee)
    db.commit()

    # Mock the request data
    employee_skill_update_data = {"skill_ids": [1, 2]}  # Assuming skill IDs to add

    # Make the request
    response = client.put(f"/employees/{test_employee_id}/updateskills/", json=employee_skill_update_data)
    
    # Clean up
    cleanup_db(db)

    # Assertions
    assert response.status_code == 200
    assert response.json() == {"message": "Employee skills updated successfully"}

# Test for unauthorized access attempt by an employee trying to update other employee's skills
def test_update_employee_skills_employee_unauthorized():
    app.dependency_overrides[get_current_user] = override_get_current_user_employee
    db = next(override_get_db())
    target_employee_id = 4  # ID of the employee to update
      # Create test skills
    skill1 = Skill(id=1, name="Python")
    skill2 = Skill(id=2, name="FastAPI")
    db.add(skill1)
    db.add(skill2)
    db.commit()
    # Mock the request data
    employee_skill_update_data = {"skill_ids": [1, 2]}  # Assuming skill IDs to add

    # Make the request
    response = client.put(f"/employees/{target_employee_id}/updateskills/", json=employee_skill_update_data)
    cleanup_db(db)

    # Assertions
    assert response.status_code == 401
    assert response.json() == {"detail": "Unauthorized"}

# Test for non-existing employee ID
def test_update_employee_skills_employee_not_found():
    app.dependency_overrides[get_current_user] = override_get_current_user_employee

    # Assuming the current user is employee with ID 1
    target_employee_id = 999  # Non-existing employee ID

    # Mock the request data
    employee_skill_update_data = {"skill_ids": [1, 2]}  # Assuming skill IDs to add

    # Make the request
    response = client.post(f"/employees/{target_employee_id}/addskills/", json=employee_skill_update_data)

    # Assertions
    assert response.status_code == 404
    assert response.json() == {"detail": "User not found"}


#############################################################################################################

#FILTER Testing


def test_filter_employees_unauthorized():
    app.dependency_overrides[get_current_user] = override_get_current_user_employee
    
    skill_ids = [1, 2]
    response = client.post("/employees/filter/", json=skill_ids)
    assert response.status_code == 401
    assert response.json() == {"detail": "Unauthorized"}

def test_filter_employees_by_skills():
    app.dependency_overrides[get_current_user] = override_get_current_user_admin

    db = next(override_get_db())
    # Create test skills
    skill1 = Skill(id=1, name="Python")
    skill2 = Skill(id=2, name="FastAPI")
    db.add(skill1)
    db.add(skill2)
    db.commit()

    # Create test employees
    employee1 = User(id=11, name="Joe", email="joe@example.com", user_type="employee", password="hashedpassword")
    employee2 = User(id=12, name="Jane", email="jane@example.com", user_type="employee", password="hashedpassword")
    employee3 = User(id=13, name="Jack", email="jack@example.com", user_type="employee", password="hashedpassword")
    db.add(employee1)
    db.add(employee2)
    db.add(employee3)
    db.commit()

    # Assign skills to employees
    emp_skill1 = EmployeeSkill(employee_id=11, skill_id=1)
    emp_skill2 = EmployeeSkill(employee_id=12, skill_id=1)
    emp_skill3 = EmployeeSkill(employee_id=12, skill_id=2)
    emp_skill4 = EmployeeSkill(employee_id=13, skill_id=2)
    db.add(emp_skill1)
    db.add(emp_skill2)
    db.add(emp_skill3)
    db.add(emp_skill4)
    db.commit()

    # Ensure no employees are assigned to projects
    skill_ids = [1,2]
    response = client.post("/employees/filter/", json=skill_ids)
    assert response.status_code == 200
    filtered_employees = response.json()
    assert len(filtered_employees) == 1
    assert filtered_employees[0]["name"] == "Jane"
    cleanup_db(db)


def test_filter_employees_no_match():
    app.dependency_overrides[get_current_user] = override_get_current_user_admin

    db = next(override_get_db())

    # Create test skills
    skill1 = Skill(id=1, name="Python")
    skill2 = Skill(id=2, name="FastAPI")
    db.add(skill1)
    db.add(skill2)
    db.commit()


    # Create test employees
    employee1 = User(id=11, name="Joe", email="joe@example.com", user_type="employee", password="hashedpassword")
    employee2 = User(id=12, name="Jane", email="jane@example.com", user_type="employee", password="hashedpassword")
    db.add(employee1)
    db.add(employee2)
    db.commit()

    # Assign skills to employees
    emp_skill1 = EmployeeSkill(employee_id=11, skill_id=1)
    emp_skill2 = EmployeeSkill(employee_id=12, skill_id=1)
    db.add(emp_skill1)
    db.add(emp_skill2)
    db.commit()

    # Ensure no employees are assigned to projects
    skill_ids = [2]  # Looking for employees with FastAPI skill
    response = client.post("/employees/filter/", json=skill_ids)
    assert response.status_code == 200
    filtered_employees = response.json()
    assert len(filtered_employees) == 0
    cleanup_db(db)
