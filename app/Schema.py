from pydantic import BaseModel
from enum import Enum


class UserType(str, Enum):
    admin = 'admin'
    employee = 'employee'
    manager = 'manager'
 
class User(BaseModel):
    name: str
    email: str
    user_type: UserType
    password: str

class ProjectCreate(BaseModel):
    name: str
    manager_id: int

class Project(BaseModel):
    name: str
    manager_id: int

class EmployeeUpdate(BaseModel):
    name: str
    email: str
    password: str
    user_type: UserType

class AssignEmployeeToProject(BaseModel):
    project_id: int
    employee_id: int

class EmployeeSkillUpdate(BaseModel):
    skill_ids: list

class RequestCreate(BaseModel):
    manager_id: int
    project_id: int
    skill_ids: list

class Request(BaseModel):
    manager_id: int
    requested_skills: str
