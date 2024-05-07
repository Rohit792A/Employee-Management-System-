from database import get_db
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from Schema import EmployeeSkillUpdate, EmployeeUpdate, User
from models import User as newuser, project_assignment, EmployeeSkill
from auth import authenticate_user

router = APIRouter(tags=["Employee related Funtions"])

#Create a new employee
@router.post("/employees/", response_model=User, dependencies=[Depends(authenticate_user('admin'))])
def create_employee(user: User, db: Session = Depends(get_db)):
    db_user = newuser(name=user.name, email=user.email, password=user.password, user_type=user.user_type)
    db.add(db_user)
    db.commit() 
    db.refresh(db_user)
    return db_user

@router.get("/employees/", response_model=list[User], dependencies=[Depends(authenticate_user)])
def get_employees(db: Session = Depends(get_db)):
    return db.query(newuser).all()

@router.delete("/employees/{employee_id}", dependencies=[Depends(authenticate_user('admin'))])
def delete_employee(employee_id: int, db: Session = Depends(get_db)):
    user = db.get(newuser, employee_id) #get row based on the primarykey 
    if user is None:
        raise HTTPException(status_code=404, detail="Employee not found")
    db.delete(user)
    db.commit()
    return {"message": "Employee deleted successfully"}

@router.put("/employees/{employee_id}", response_model=User, dependencies=[Depends(authenticate_user('admin'))])
def update_employee(employee_id: int, employee_data: EmployeeUpdate, db: Session = Depends(get_db)):
    user = db.get(newuser, employee_id)
    if user is None:
        raise HTTPException(status_code=404, detail="Employee not found")
    user.name = employee_data.name
    user.email = employee_data.email
    user.password = employee_data.password
    user.user_type = employee_data.user_type
    db.commit()
    db.refresh(user)
    return user

@router.put("/employees/{employee_id}/skills/", response_model=dict, dependencies=[Depends(authenticate_user('admin'))])
def update_employee_skills(employee_id: int, skills: EmployeeSkillUpdate, db: Session = Depends(get_db)):
    # Delete existing skills
    db.query(EmployeeSkill).filter(EmployeeSkill.employee_id == employee_id).delete()
    
    # Add new skills
    for skill_id in skills.skill_ids:
        employee_skill = EmployeeSkill(employee_id=employee_id, skill_id=skill_id)
        db.add(employee_skill)
    db.commit()
    return {"message": "Employee skills updated successfully"}

@router.post("/employees/filter/", response_model=list[User])
def filter_employees_by_skills(skill_ids: list[int], db: Session = Depends(get_db)):
    # Get all employees not assigned to any project
    unassigned_employees = db.query(newuser).filter(~newuser.id.in_(db.query(project_assignment.employee_id))).all()
    
    # Filter employees by requested skills
    filtered_employees = []
    for employee in unassigned_employees:
        if all(skill_id in [s.id for s in employee.skills] for skill_id in skill_ids):
            filtered_employees.append(employee)
    return filtered_employees
