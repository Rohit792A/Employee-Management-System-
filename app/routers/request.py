from Schema import Request, RequestCreate
from fastapi import APIRouter, Depends, HTTPException,Request
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from models import Request as newreq,User as newuser,Project as newproj,Project_assignment as proj_as
from Schema import RequestStatus,RequestCreate
from sqlalchemy.orm import Session
from database import get_db
from routers.auth import get_current_user


router = APIRouter(tags=["Requests related Functions"])

templates = Jinja2Templates(directory="..\\frontend\\templates\\request")


# Create a new request for emp
@router.post("/add_new_request/", response_model=RequestCreate)
def request_employees(request_data: RequestCreate, db: Session = Depends(get_db),cu : dict = Depends(get_current_user)):

    user_id = cu["id"]
    
    #check if a user with given id is in db else error
    user = db.get(newuser, user_id)
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    
    # check if user_type is manager
    if user.user_type != "manager":
        raise HTTPException(status_code=401, detail="You are not authorized to perform this action")


    # check if the manager id is present in newuser table
    manager_id = request_data.manager_id
    manager = db.get(newuser, manager_id)
    if manager is None:
        raise HTTPException(status_code=404, detail="Manager not found")
    
    # check if the project_id is present in project table
    project_id = request_data.project_id
    project = db.get(newproj, project_id)
    if project is None:
        raise HTTPException(status_code=404, detail="Project not found")    
        
    # check if the manager is not assigned to the project raise error
    if project.manager_id !=manager_id:
        raise HTTPException(status_code=401, detail="Manager is not assigned to project")

    # create a new request and add to the db 
    new_request = newreq(
        manager_id=request_data.manager_id,
        project_id=request_data.project_id,
        requested_emp_id=request_data.requested_emp_id
        )
    db.add(new_request)
    db.commit()
    db.refresh
    return new_request
    
    
# method to get all the requests from requests table
@router.get("/requests/", response_model=list[RequestStatus])
def get_requests(db: Session = Depends(get_db),cu : dict = Depends(get_current_user)):

    user_id = cu["id"]

    # check if a user with given id is in db else error
    user = db.get(newuser, user_id)
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    
    # check if user_type is admin or manager
    if user.user_type not in ["admin", "manager"]:
        raise HTTPException(status_code=401, detail="You are not authorized to perform this action")

    # check if there are entries in request table
    request_entries = db.query(newreq).order_by(newreq.id).all()
    if not request_entries:
        raise HTTPException(status_code=404, detail="No requests found")
    return request_entries
    

# Function to approve any request with request_id
@router.put("/requests/{request_id}/approve/", response_model=RequestStatus)
def approve_request(request_id: int, db: Session = Depends(get_db),cu : dict = Depends(get_current_user)):
    
    user_id = cu["id"]

    # check if a user with given id is in db else error
    user = db.get(newuser, user_id)
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    
    # check if user_type is admin 
    if user.user_type != "admin":
        raise HTTPException(status_code=401, detail="You are not authorized to perform this action")

    request = db.get(newreq, request_id)
    if request is None:
        raise HTTPException(status_code=404, detail="Request not found")

        
    # Get all unassigned employees
    subquery = db.query(proj_as.employee_id).subquery()     #get all empid from project_assignment table
    unassigned_employees = db.query(newuser).filter(newuser.id.notin_(subquery)).all()  #remove the employees present in the project_assignment table
    
    # if available assign to project and update request status
    if request.requested_emp_id in [emp.id for emp in unassigned_employees]:
        #assign to project
        new_assignment = proj_as(employee_id=request.requested_emp_id,project_id=request.project_id)
        db.add(new_assignment)
        db.commit()
        db.refresh(new_assignment)

        #update request status
        request.status = 'approved'
        db.commit()
        db.refresh(request)
        return request
         
    #if not available raise error
    else:
        raise HTTPException(status_code=404, detail="Employee not available")


# Function to reject any request with request_id
@router.put("/requests/{request_id}/reject/", response_model=RequestStatus)
def reject_request(request_id: int, db: Session = Depends(get_db),cu : dict = Depends(get_current_user)):
    
    user_id = cu["id"]

    #check if a user with given id is in db else error
    user = db.get(newuser, user_id)
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    
    # check if user_type is admin 
    if user.user_type != "admin":
        raise HTTPException(status_code=401, detail="You are not authorized to perform this action")

    request = db.get(newreq, request_id)

    if request is None:
        raise HTTPException(status_code=404, detail="Request not found")
    
    # if already approved than raise error
    elif request.status == 'approved':
        raise HTTPException(status_code=404, detail="Request already approved")
    else:
        # update request status
        request.status ='rejected'
        db.commit()
        db.refresh(request)
        return request


# delete request with requestid 
@router.delete("/requests/{request_id}")
def delete_request(request_id: int, db: Session = Depends(get_db),cu : dict = Depends(get_current_user)):
    
    user_id = cu["id"]
    #check if a user with given id is in db else error
    user = db.get(newuser, user_id)
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    
    #check if user_type is admin 
    if user.user_type != "admin":
        raise HTTPException(status_code=401, detail="You are not authorized to perform this action")
    
    request = db.get(newreq, request_id) #get row based on the primarykey 
    if request is None:
        raise HTTPException(status_code=404, detail="Request not found")
    db.delete(request)
    db.commit()
    return {"message": "Request deleted successfully"}



#################################################################################################################################

# Functions to render html pages

@router.get('/get_req/',response_class=HTMLResponse)
def index(request: Request):
    context = {'request' : request}
    return templates.TemplateResponse("get_requests.html",context)


@router.get('/create_req/',response_class=HTMLResponse)
def index(request: Request):
    context = {'request' : request}
    return templates.TemplateResponse("create_request.html",context)


@router.get('/approve_req/',response_class=HTMLResponse)
def index(request: Request):
    context = {'request' : request}
    return templates.TemplateResponse("approve_req.html",context)

@router.get('/reject_req/',response_class=HTMLResponse)
def index(request: Request):
    context = {'request' : request}
    return templates.TemplateResponse("reject_req.html",context)

@router.get('/delete_req/',response_class=HTMLResponse)
def index(request: Request):
    context = {'request' : request}
    return templates.TemplateResponse("delete_req.html",context)

@router.get('/get_req_status/',response_class=HTMLResponse)
def index(request: Request):
    context = {'request' : request}
    return templates.TemplateResponse("get_req_status.html",context)