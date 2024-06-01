from database import get_db
from fastapi import APIRouter, Depends, HTTPException,Request
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session
from Schema import EmployeeSkillUpdate, EmployeeUpdate, User,Skills,User_with_id,Skillname
from models import User as newuser,Project as newproj, Project_assignment, EmployeeSkill,Skill as allskills,Request as newreq
# from auth import authenticate_user
# from routers.auth import get_current_user,bcrypt_context
from routers.auth import bcrypt_context,get_current_user

router = APIRouter(tags=["Employee related Funtions"])
# cu = get_current_user

templates = Jinja2Templates(directory="..\\frontend\\templates\\employee")

#Create a new employee
@router.post("/Create-employees/", response_model=User_with_id)
def create_employee(user: User, db: Session = Depends(get_db),cu : dict = Depends(get_current_user)):
    user_id = cu["id"]
    c_user = db.get(newuser, user_id)
    #if user is not present or is not admin raise error
    if not c_user or c_user.user_type != 'admin':
        raise HTTPException(status_code=401, detail="Unauthorized")
    
    db_user = newuser(
        name=user.name, 
        email=user.email, 
        password=bcrypt_context.hash(user.password),
        user_type=user.user_type
        )
    db.add(db_user)
    db.commit() 
    db.refresh(db_user)
    return db_user


@router.get("/employees/" ,response_model=list[User_with_id])
def get_employees(db: Session = Depends(get_db),cu : dict = Depends(get_current_user)):
    user_id = cu["id"]
    user = db.get(newuser, user_id)
    
    user_entries = db.query(newuser).order_by(newuser.id).all()
    
    if user_entries:
        return user_entries
    else:
        raise HTTPException(status_code=404, detail="No user found")

@router.delete("/employees/{employee_id}")
def delete_employee(employee_id: int, db: Session = Depends(get_db),cu : dict = Depends(get_current_user)):
    user_id = cu["id"]
    user = db.get(newuser, user_id)
    #if user is not present or is not admin raise error
    if not user or user.user_type != 'admin':
        raise HTTPException(status_code=401, detail="Unauthorized")
    
    emp = db.get(newuser, employee_id) #get row based on the primarykey 
    if emp is None:
        raise HTTPException(status_code=404, detail="Employee not found")
    db.delete(emp)
    db.commit()
    return {"message": "Employee deleted successfully"}

@router.get("/employeedetails/{employee_id}", response_model=None)
def get_employee_details(employee_id: int, db: Session = Depends(get_db),cu : dict = Depends(get_current_user)):
    
    #if user is present and manager can view emp details ans emp can only view his own details
    user_id = cu["id"]
    user = db.get(newuser, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    #emp can only view his own details
    if user.user_type== 'employee':
        if employee_id!=user_id:
            raise HTTPException(status_code=401, detail="Unauthorized")
    
    #manager can view only his own and emp details
    elif user.user_type =='manager':
        employee = db.query(newuser).filter(newuser.id == employee_id).first()
        if employee or employee_id==user_id:
            pass
        else:
            raise HTTPException(status_code=401, detail="Unauthorized")

    # get the employee details

    employee = db.query(newuser).filter(newuser.id == employee_id).first()
    if not employee:
        raise HTTPException(status_code=404, detail="Employee not found")

    # Fetch projects assigned to the employee
    projects = db.query(newproj).join(Project_assignment).filter(Project_assignment.employee_id == employee_id).all()
    
    emp_proj = []
    if projects is None:
        emp_proj = []
    else:
        #create a list of dict with id and name
        for project in projects:
            emp_proj.append({"id": project.id, "name": project.name})

    # Fetch skills of the employee
    skills = db.query(allskills).join(EmployeeSkill).filter(EmployeeSkill.employee_id == employee_id).all()
    if skills == None:
        emp_skills = []
    else:
        #create a list of dict with id and name
        emp_skills = []
        for skill in skills:
            emp_skills.append({"id": skill.id, "name": skill.name})


    #get the manager id from the project table
    mang_id=db.query(newproj).join(Project_assignment).filter(Project_assignment.employee_id == employee_id).first()
    if mang_id:
            manager_id = mang_id.manager_id
            manager_name=db.query(newuser).filter(newuser.id == manager_id).first().name
    else:
        manager_id = "N/A"
        manager_name = "N/A"
    
    # Structure the response
    employee_detail = {
        "id": employee.id,
        "name": employee.name,
        "email": employee.email,
        "user_type": employee.user_type,
        "projects": emp_proj,
        "manager id":manager_id,
        "manager name":manager_name,
        "skills": emp_skills
    }
    return employee_detail


@router.put("/employees/{employee_id}", response_model=User)
def update_employee(employee_id: int, employee_data: EmployeeUpdate, db: Session = Depends(get_db),cu : dict = Depends(get_current_user)):
    user_id = cu["id"]
    user = db.get(newuser, user_id)
    #if user is not present or is not admin raise error
    if not user or user.user_type != 'admin':
        raise HTTPException(status_code=401, detail="Unauthorized")
    
    #check if a user with given id is in db else error
    emp = db.get(newuser, employee_id)
    if emp is None:
        raise HTTPException(status_code=404, detail="Employee not found")
    emp.name = employee_data.name
    emp.email = employee_data.email
    emp.password = employee_data.password
    emp.user_type = employee_data.user_type
    db.commit()
    db.refresh(emp)
    return emp

#create a endpoint to add new skills in db
@router.post("/new_skills", response_model=dict)
def create_skill(skill: Skillname, db: Session = Depends(get_db), cu: dict = Depends(get_current_user)):
    user_id = cu["id"]
    user = db.get(newuser, user_id)
    # if user is not present or is not admin raise error
    if not user or user.user_type != 'admin':
        raise HTTPException(status_code=401, detail="Unauthorized")
    #if skill name already exists
    if db.query(allskills).filter(allskills.name == skill.name).first():
        raise HTTPException(status_code=400, detail="Skill already exists")

    db_skill = allskills(name=skill.name)
    db.add(db_skill)
    db.commit()
    db.refresh(db_skill)
    return {"message": "Skill added successfully"}
    #create a endpoint to delete skills in db
@router.delete("/skills/{skill_id}", response_model=dict)
def delete_skill(skill_id: int, db: Session = Depends(get_db),cu : dict = Depends(get_current_user)):
    user_id = cu["id"]
    user = db.get(newuser, user_id)
        #if user is not present or is not admin raise error
    if not user or user.user_type != 'admin':
        raise HTTPException(status_code=401, detail="Unauthorized")
        
    skill = db.get(allskills, skill_id)
    if skill is None:
        raise HTTPException(status_code=404, detail="Skill not found")
    db.delete(skill)
    db.commit()
    return {"message": "Skill deleted successfully"}


@router.post("/employees/{employee_id}/addskills/", response_model=dict)
def add_employee_skills(employee_id: int, skills: EmployeeSkillUpdate, db: Session = Depends(get_db),cu : dict = Depends(get_current_user)):
    user_id = cu["id"]
    user = db.get(newuser, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    #emp can only update his own skills
    if user.user_type== 'employee':
        if employee_id!=user_id:
            raise HTTPException(status_code=401, detail="Unauthorized")
        
    #manager can update only his own and emp skills
    if user.user_type== 'manager':
        employee = db.query(newuser).filter(newuser.id == employee_id).first()
        if employee or employee_id==user_id:
            pass
        else:
            raise HTTPException(status_code=401, detail="Unauthorized")


    #check if a user with given id is in db else error
    emp = db.get(newuser, employee_id)
    if emp is None:
        raise HTTPException(status_code=404, detail="Employee not found")   
    
    # Add new skills
    for skill_id in skills.skill_ids:
        employee_skill = EmployeeSkill(employee_id=employee_id, skill_id=skill_id)
        db.add(employee_skill)
    db.commit()
    return {"message": "Employee skills updated successfully"}


# @router.put("/employees/{employee_id}/skills/", response_model=dict, dependencies=[Depends(authenticate_user('admin'))])
@router.put("/employees/{employee_id}/updateskills/", response_model=dict)
def update_employee_skills(employee_id: int, skills: EmployeeSkillUpdate, db: Session = Depends(get_db),cu : dict = Depends(get_current_user)):
    
    user_id = cu["id"]
    user = db.get(newuser, user_id)
    #if user is not present or is not admin raise error
    if not user or user.user_type != 'admin':
        raise HTTPException(status_code=401, detail="Unauthorized")

    #check if a user with given id is in db else error
    emp = db.get(newuser, employee_id)
    if emp is None:
        raise HTTPException(status_code=404, detail="Employee not found")
    
    # Delete existing skills
   
    db.query(EmployeeSkill).filter(EmployeeSkill.employee_id == employee_id).delete()
   
    
    # Add new skills
    for skill_id in skills.skill_ids:
        employee_skill = EmployeeSkill(employee_id=employee_id, skill_id=skill_id)
        db.add(employee_skill)
    db.commit()
    return {"message": "Employee skills updated successfully"}

@router.post("/employees/filter/", response_model=list[User_with_id])
def filter_employees_by_skills(skill_ids: list[int], db: Session = Depends(get_db),cu : dict = Depends(get_current_user)):
    user_id = cu["id"]
    user = db.get(newuser, user_id)
    #if user is not present or is not admin or manager raise error
    if not user or user.user_type not in ['admin', 'manager']:
        raise HTTPException(status_code=401, detail="Unauthorized")

    # Get all unassigned employees
    subquery = db.query(Project_assignment.employee_id)     #get all empid from project_assignment table
    unassigned_employees = db.query(newuser).filter(newuser.id.notin_(subquery)).all()  #remove the employees present in the project_assignment table

    # Filter employees by requested skills
    filtered_employees = []
    for employee in unassigned_employees:
        employee_skills = {es.skill_id for es in db.query(EmployeeSkill).filter(EmployeeSkill.employee_id == employee.id).all()}
        if set(skill_ids).issubset(employee_skills):
            filtered_employees.append(employee)

    return filtered_employees

#get the skills table show skill id and name of all skills 
@router.get("/skills/",response_model=list[Skills])
def get_all_skills(db: Session = Depends(get_db),cu : dict = Depends(get_current_user)):
    user_id = cu["id"]
    user = db.get(newuser, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    skill_enteries = db.query(allskills).all()

    if skill_enteries:
        return skill_enteries
    else:
        raise HTTPException(status_code=404, detail="No skill found")



@router.get('/getempdata/',response_class=HTMLResponse)
def index(request: Request ,db: Session = Depends(get_db),cu : dict = Depends(get_current_user)):
    
    context = {'request' : request}
    #check if user exists and user type is admin then render else 401 error
    if cu is None or cu["user_type"]!="admin":
        return templates.TemplateResponse("unauthenticated.html",context,status_code=401)
    return templates.TemplateResponse("empdta.html",context)

@router.get('/addempdata/',response_class=HTMLResponse)
def index(request: Request):
    context = {'request' : request}
    return templates.TemplateResponse("addemp.html",context)

@router.get('/deleteemp/',response_class=HTMLResponse)
def index(request: Request):
    context = {'request' : request}
    return templates.TemplateResponse("deleteemp.html",context)


@router.get('/updateemp/',response_class=HTMLResponse)
def index(request: Request):
    context = {'request' : request}
    return templates.TemplateResponse("updateemp.html",context)


@router.get('/viewskills/',response_class=HTMLResponse)
def index(request: Request):
    context = {'request' : request}
    return templates.TemplateResponse("viewskills.html", context)

@router.get('/add_new_skill/',response_class=HTMLResponse)
def index(request: Request):
    context = {'request' : request}
    return templates.TemplateResponse("add_new_skill.html", context)

@router.get('/delete_skill/',response_class=HTMLResponse)
def index(request: Request):
    context = {'request' : request}
    return templates.TemplateResponse("delete_skill.html", context)


@router.get('/addskills/',response_class=HTMLResponse)
def index(request: Request):
    context = {'request' : request}
    return templates.TemplateResponse("addskills.html", context)

@router.get('/updateskills/',response_class=HTMLResponse)
def index(request: Request):
    context = {'request' : request}
    return templates.TemplateResponse("updateskills.html", context)

@router.get('/filter_emp_by_skills/',response_class=HTMLResponse)
def index(request: Request):
    context = {'request' : request}
    return templates.TemplateResponse("filter_emp_by_skills.html", context)

#for users_for_emp.html
@router.get('/users_for_emp/',response_class=HTMLResponse)
def index(request: Request):
    context = {'request' : request}
    return templates.TemplateResponse("users_for_emp.html", context)


#endpoint for update password by emp id


