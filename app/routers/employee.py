from database import get_db
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from Schema import EmployeeSkillUpdate, EmployeeUpdate, User
from models import User as newuser, Project_assignment, EmployeeSkill
# from auth import authenticate_user
from routers.auth import get_current_user,bcrypt_context

router = APIRouter(tags=["Employee related Funtions"])
cu = get_current_user


#Create a new employee
# @router.post("/employees/", response_model=User, dependencies=[Depends(authenticate_user('admin'))])
@router.post("/employees/", response_model=User)
def create_employee(user: User, db: Session = Depends(get_db)):
    # if not cuser:
    #     raise HTTPException(status_code=401, detail="Unauthorized")
    db_user = newuser(name=user.name, email=user.email, password=bcrypt_context.hash(user.password),user_type=user.user_type)
    db.add(db_user)
    db.commit() 
    db.refresh(db_user)
    return db_user

# @router.get("/employees/", response_model=list[User], dependencies=[Depends(authenticate_user)])
@router.get("/employees/", response_model=list[User])
def get_employees(db: Session = Depends(get_db),cuser : dict=Depends(get_current_user)):
    if not cuser:
        raise HTTPException(status_code=401, detail="Unauthorized")
    role = cuser['role']
    if role == 'admin':
        user_entries =  db.query(newuser).all()
    elif role == 'employee':
        user_entries =  db.query(newuser).filter(newuser.user_type == 'employee' or newuser.user_type == 'manager').all()
    elif role == 'manager':
        user_entries =  db.query(newuser).filter(newuser.user_type == 'employee' or newuser.user_type == 'manager').all()
    else:
        raise HTTPException(status_code=403, detail="Forbidden")


    return user_entries

# @router.delete("/employees/{employee_id}", dependencies=[Depends(authenticate_user('admin'))])
@router.delete("/employees/{employee_id}")
def delete_employee(employee_id: int, db: Session = Depends(get_db),cuser : dict=Depends(get_current_user)):
    if not cuser or not cuser['role']=='admin':
        raise HTTPException(status_code=401, detail="Can only be accessed by admin")
    user = db.get(newuser, employee_id) #get row based on the primarykey 
    if user is None:
        raise HTTPException(status_code=404, detail="Employee not found")
    db.delete(user)
    db.commit()
    return {"message": "Employee deleted successfully"}

# @router.put("/employees/{employee_id}", response_model=User, dependencies=[Depends(authenticate_user('admin'))])
@router.put("/employees/{employee_id}", response_model=User)
def update_employee(employee_id: int, employee_data: EmployeeUpdate, db: Session = Depends(get_db),cuser : dict=Depends(get_current_user)):
    if not cuser or not cuser['role']=='admin' :
        raise HTTPException(status_code=401, detail="Can only be accessed by admin")
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

# @router.put("/employees/{employee_id}/skills/", response_model=dict, dependencies=[Depends(authenticate_user('admin'))])
@router.put("/employees/{employee_id}/skills/", response_model=dict)
def update_employee_skills(employee_id: int, skills: EmployeeSkillUpdate, db: Session = Depends(get_db),cuser : dict=Depends(get_current_user)):
    # Delete existing skills
    if not cuser:
        raise HTTPException(status_code=401, detail="Unauthorized")
    db.query(EmployeeSkill).filter(EmployeeSkill.employee_id == employee_id).delete()
    
    # Add new skills
    for skill_id in skills.skill_ids:
        employee_skill = EmployeeSkill(employee_id=employee_id, skill_id=skill_id)
        db.add(employee_skill)
    db.commit()
    return {"message": "Employee skills updated successfully"}

@router.post("/employees/filter/", response_model=list[User])
def filter_employees_by_skills(skill_ids: list[int], db: Session = Depends(get_db),cuser: dict= Depends(get_current_user)):

    if not cuser or not cuser['role']=='manager':
        raise HTTPException(status_code=401, detail="Can only be accessed by manager")
    # Get all employees not assigned to any project
    unassigned_employees = db.query(EmployeeSkill).filter(~newuser.id.in_(db.query(Project_assignment.employee_id))).all()
    # unassigned_employees = db.query(Project_assignment.employee_id).all()

    # Filter employees by requested skills
    filtered_employees = []
    for employee in unassigned_employees:
        if all(skill_id in [s.id for s in employee.skills] for skill_id in skill_ids):
            filtered_employees.append(employee)
    return filtered_employees
