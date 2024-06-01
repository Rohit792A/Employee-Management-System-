from sqlalchemy.orm import Session
from fastapi import APIRouter, Depends,HTTPException,Request
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from database import get_db
from Schema import AssignEmployeeToProject, ProjectCreate, Project 
from models import User as newuser,Project as newproj, Project_assignment as proj_as
from .auth import authenticate_user
from fastapi import APIRouter, Depends
from routers.auth import bcrypt_context,get_current_user

router = APIRouter(tags= ["Project related Functions"])

templates = Jinja2Templates(directory="..\\frontend\\templates\\project")

@router.post("/create_projects/", response_model=Project)
def create_project(project: ProjectCreate, db: Session = Depends(get_db),cu : dict =Depends(get_current_user)):
    user_id = cu["id"]
    user = db.get(newuser, user_id)
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    
    #check if project.manager id is a manager
    manager_id = project.manager_id
    manager = db.get(newuser, manager_id)
    if manager is None or manager.user_type!="manager":
        raise HTTPException(status_code=404, detail="Manager not found")
    
    #check if the user is manager 
    if user.user_type not in ["admin","manager"]:
        raise HTTPException(status_code=401, detail="You are not authorized to perform this action")

    db_project = newproj(name=project.name, manager_id=project.manager_id)
    db.add(db_project)
    db.commit()
    db.refresh(db_project)
    return db_project

@router.get("/projects/", response_model=list[Project])
def get_projects(db: Session = Depends(get_db),cu : dict =Depends(get_current_user)):

    user_id = cu["id"]
    user = db.get(newuser, user_id)
    if user is None or user.user_type not in ["admin","manager"]:
        raise HTTPException(status_code=401, detail="You are not authorized to perform this action")
    
    project_enteries = db.query(newproj).order_by(newproj.id).all()
    if project_enteries:
        return project_enteries
    else:
        raise HTTPException(status_code=404, detail="No projects found")

#check project_assignment status using proj_as table
@router.get("/projects_assigned/",response_model=list[AssignEmployeeToProject])
def get_assigned_all(db: Session = Depends(get_db),cu : dict =Depends(get_current_user)):
    user_id = cu["id"]
    user = db.get(newuser, user_id)
    if user is None or user.user_type not in ["admin","manager"]:
        raise HTTPException(status_code=401, detail="You are not authorized to perform this action")
    

#get all the alloted projects and emp from the project_assignment table
    assigned_projects = db.query(proj_as).all()
    if assigned_projects:
        return assigned_projects
    else:
        raise HTTPException(status_code=404, detail="No projects found")

@router.post("/projects/assign_employee", response_model=dict)
def assign_employee_to_project(assignment: AssignEmployeeToProject, db: Session = Depends(get_db),cu : dict =Depends(get_current_user)):
    user_id = cu["id"]
    user = db.get(newuser, user_id)
    if user is None or user.user_type!= "admin":
        raise HTTPException(status_code=401, detail="You are not authorized to perform this action")
    
    #Check if assignment.employee_id and assignment.project_id is in db else raise error
    user = db.get(newuser, assignment.employee_id)
    if user is None:
        raise HTTPException(status_code=404, detail="Employee not found")
    project = db.get(newproj, assignment.project_id)
    if project is None:
        raise HTTPException(status_code=404, detail="Project not found")
    
    #check if employee is already assigned to the project else raise error
    assign_query = db.query(proj_as).filter(
        (proj_as.employee_id == assignment.employee_id) &
        (proj_as.project_id == assignment.project_id)
        ) 
    if assign_query.all():
        raise HTTPException(status_code=404, detail="Employee already assigned to project")
    
    #assign employee to the project
    assign_proj = proj_as(employee_id=assignment.employee_id, project_id=assignment.project_id)
    db.add(assign_proj)
    db.commit()
    db.refresh(assign_proj)
    return {"message": "Employee assigned to project"}

@router.delete("/projects/unassign_employee/{employee_id}", response_model=dict)
def unassign_employee_from_project(employee_id: int, db: Session = Depends(get_db),cu : dict =Depends(get_current_user)):
    user_id = cu["id"]
    user = db.get(newuser, user_id)
    if user is None or user.user_type!= "admin":
        raise HTTPException(status_code=401, detail="You are not authorized to perform this action")
    
    # Check if the employee exists
    user = db.get(newuser,employee_id)
    if user is None:
        raise HTTPException(status_code=404, detail="Employee not found")
    
    # Check if the employee is assigned to the project
    assignment = db.query(proj_as).filter(
        (proj_as.employee_id ==  employee_id)
    ).first()
    
    if assignment is None:
        raise HTTPException(status_code=404, detail="Employee not assigned to any project")
    
    # Delete the assignment
    db.delete(assignment)
    db.commit()
    
    return {"message": "Employee unassigned from project"}


@router.get('/add_proj/',response_class=HTMLResponse)
def index(request: Request):
    context = {'request' : request}
    return templates.TemplateResponse("add_project.html",context)


@router.get('/get_proj/',response_class=HTMLResponse)
def index(request: Request):
    context = {'request' : request}
    return templates.TemplateResponse("get_project.html",context)

@router.get('/assigned_proj/',response_class=HTMLResponse)
def index(request: Request):
    context = {'request' : request}
    return templates.TemplateResponse("assigned_proj.html",context)

@router.get('/assign_emp/',response_class=HTMLResponse)
def index(request: Request):
    context = {'request' : request}
    return templates.TemplateResponse("assign_emp.html",context)


@router.get('/unassign_emp/',response_class=HTMLResponse)
def index(request: Request):
    context = {'request' : request}
    return templates.TemplateResponse("unassign_emp.html",context)
