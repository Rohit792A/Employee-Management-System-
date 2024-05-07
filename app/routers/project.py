from sqlalchemy.orm import Session
from fastapi import APIRouter, Depends
from database import get_db
from Schema import AssignEmployeeToProject, ProjectCreate, Project 
from models import Project as newproj, project_assignment
from auth import authenticate_user
from fastapi import APIRouter, Depends

router = APIRouter(tags= ["Project related Functions"])

@router.post("/projects/", response_model=Project, dependencies=[Depends(authenticate_user('manager'))])
def create_project(project: ProjectCreate, db: Session = Depends(get_db)):
    db_project = newproj(name=project.name, manager_id=project.manager_id)
    db.add(db_project)
    db.commit()
    db.refresh(db_project)
    return db_project

@router.get("/projects/", response_model=list[Project], dependencies=[Depends(authenticate_user)])
def get_projects(db: Session = Depends(get_db)):
    return db.query(newproj).all()

@router.post("/projects/assign_employee", response_model=dict, dependencies=[Depends(authenticate_user('manager'))])
def assign_employee_to_project(assignment: AssignEmployeeToProject, db: Session = Depends(get_db)):
    assignment_query = project_assignment.insert().values(employee_id=assignment.employee_id, project_id=assignment.project_id)
    db.execute(assignment_query)
    db.commit()
    return {"message": "Employee assigned to project"}

@router.delete("/projects/unassign_employee", response_model=dict, dependencies=[Depends(authenticate_user('manager'))])
def unassign_employee_from_project(unassignment: AssignEmployeeToProject, db: Session = Depends(get_db)):
    unassignment_query = project_assignment.delete().where(project_assignment.c.employee_id == unassignment.employee_id, project_assignment.c.project_id == unassignment.project_id)
    db.execute(unassignment_query)
    db.commit()
    return {"message": "Employee unassigned from project"}
