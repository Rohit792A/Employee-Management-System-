from sqlalchemy import Column, Integer, String, Enum, ForeignKey, Table,PrimaryKeyConstraint
from sqlalchemy.orm import relationship
from database import Base

class User(Base):
    __tablename__ = 'Users'
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    email = Column(String(255), unique=True, nullable=False)
    password = Column(String(255), nullable=False)
    user_type = Column(Enum('admin', 'employee', 'manager', name="roletypes"), nullable=False)

class Project(Base):
    __tablename__ = 'Projects'
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    manager_id = Column(Integer, ForeignKey('Users.id'), nullable=True)

    # Define a many-to-one relationship between Project and User
    manager = relationship('User', backref='projects')

# Define the many-to-many relationship between Users and Projects
# project_assignment = Table(
#     'project_assignment',
#     Base.metadata,
#     Column('project_id', Integer, ForeignKey('Projects.id')),
#     Column('employee_id', Integer, ForeignKey('Users.id')),
#     PrimaryKeyConstraint('employee_id')
# )
class Project_assignment(Base) : 
    __tablename__ = 'project_assignment'
    project_id = Column(Integer, ForeignKey('Projects.id'),nullable = False)
    employee_id = Column(Integer, ForeignKey('Users.id'),nullable = False,primary_key = True)


class Skill(Base):
    __tablename__ = 'Skills'
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)

class Request(Base):
    __tablename__ = 'Requests'
    id = Column(Integer, primary_key=True, index=True)
    manager_id = Column(Integer, ForeignKey('Users.id'), nullable=False)
    project_id = Column(Integer, ForeignKey('Projects.id'),nullable=False )
    requested_emp_id = Column(Integer, nullable=False)
    status = Column(Enum('pending', 'approved', 'rejected', name='request_status'), nullable=False, default='pending')

    # Define a many-to-one relationship between Request and User
    project = relationship('Project', backref='requests')
    manager = relationship('User', backref='requests')


# employee_assignment = Table(
#     'employee_assignment',
#     Base.metadata,
#     Column('request_id', Integer, ForeignKey('Requests.id')),
#     Column('employee_id', Integer, ForeignKey('Users.id')),
#     PrimaryKeyConstraint('request_id')
# )

class Employee_assignment(Base) : 
    __tablename__ = 'employee_assignment'
    request_id = Column(Integer, ForeignKey('Requests.id'),nullable = False,primary_key = True)
    employee_id = Column(Integer, ForeignKey('Users.id'),nullable = False)


class EmployeeSkill(Base):
    __tablename__ = 'Employee_Skills'
    employee_id = Column(Integer, ForeignKey('Users.id'), primary_key=True)
    skill_id = Column(Integer, ForeignKey('Skills.id'), primary_key=True)

    # Define a many-to-one relationship between EmployeeSkill and User
    employee = relationship('User', backref='Skills')

    # Define a many-to-one relationship between EmployeeSkill and Skill
    skill = relationship('Skill', backref='employees')
