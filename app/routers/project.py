from sqlalchemy.orm import Session
from fastapi import APIRouter, Depends,HTTPException
from database import get_db
from Schema import AssignEmployeeToProject, ProjectCreate, Project 
from models import User as newuser,Project as newproj, Project_assignment as proj_as
from .auth import authenticate_user
from fastapi import APIRouter, Depends
from routers.auth import get_current_user,bcrypt_context

router = APIRouter(tags= ["Project related Functions"])

# @router.post("/projects/", response_model=Project, dependencies=[Depends(authenticate_user('manager'))])
@router.post("/projects/", response_model=Project)
def create_project(project: ProjectCreate, db: Session = Depends(get_db),cuser : dict=Depends(get_current_user)):
    if not cuser or not cuser['role']=='admin' :
        raise HTTPException(status_code=401, detail="Can only be accessed by admin")
    db_project = newproj(name=project.name, manager_id=project.manager_id)
    db.add(db_project)
    db.commit()
    db.refresh(db_project)
    return db_project

# @router.get("/projects/", response_model=list[Project], dependencies=[Depends(authenticate_user)])
@router.get("/projects/", response_model=list[Project])
def get_projects(db: Session = Depends(get_db),cuser : dict=Depends(get_current_user)):
    if not cuser:
        raise HTTPException(status_code=401, detail="Unauthorized")
    role = cuser['role']
    if role in  ['admin','employee','manager']:
      return db.query(newproj).all()
    else:
        raise HTTPException(status_code=403, detail="Forbidden")

# @router.post("/projects/assign_employee", response_model=dict, dependencies=[Depends(authenticate_user('manager'))])
@router.post("/projects/assign_employee", response_model=dict)
def assign_employee_to_project(assignment: AssignEmployeeToProject, db: Session = Depends(get_db),cuser : dict=Depends(get_current_user)):
    if not cuser or not cuser['role']=='admin' :
        raise HTTPException(status_code=401, detail="Can only be accessed by admin")
    assignment_query = proj_as.insert().values(employee_id=assignment.employee_id, project_id=assignment.project_id)
    db.execute(assignment_query)
    db.commit()
    return {"message": "Employee assigned to project"}

# @router.delete("/projects/unassign_employee", response_model=dict, dependencies=[Depends(authenticate_user('manager'))])
@router.delete("/projects/unassign_employee", response_model=dict)
def unassign_employee_from_project(unassignment: AssignEmployeeToProject, db: Session = Depends(get_db),cuser : dict=Depends(get_current_user)):
    if not cuser or not cuser['role']=='admin' :
        raise HTTPException(status_code=401, detail="Can only be accessed by admin")
    unassignment_query = proj_as.delete().where(proj_as.c.employee_id == unassignment.employee_id, proj_as.c.project_id == unassignment.project_id)
    db.execute(unassignment_query)
    db.commit()
    return {"message": "Employee unassigned from project"}
