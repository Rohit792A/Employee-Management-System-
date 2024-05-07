from Schema import Request, RequestCreate
from fastapi import APIRouter, Depends, HTTPException
from models import Request as newreq
from sqlalchemy.orm import Session
from database import get_db
from auth import authenticate_user

router = APIRouter(tags=["Requests related Functions"])

@router.post("/requests/", response_model=Request, dependencies=[Depends(authenticate_user('manager'))])
def request_employees(request_data: RequestCreate, db: Session = Depends(get_db)):
    request = newreq(manager_id=request_data.manager_id, requested_skills=','.join(map(str, request_data.skill_ids)))
    db.add(request)
    db.commit()
    db.refresh(request)
    return request

@router.put("/requests/{request_id}/approve/", response_model=Request, dependencies=[Depends(authenticate_user('admin'))])
def approve_request(request_id: int, db: Session = Depends(get_db)):
    request = db.get(newreq, request_id)
    if request is None:
        raise HTTPException(status_code=404, detail="Request not found")
    request.status = 'approved'
    db.commit()
    db.refresh(request)
    return request

@router.put("/requests/{request_id}/reject/", response_model=Request, dependencies=[Depends(authenticate_user('admin'))])
def reject_request(request_id: int, db: Session = Depends(get_db)):
    request = db.get(newreq, request_id)
    if request is None:
        raise HTTPException(status_code=404, detail="Request not found")
    request.status = 'rejected'
    db.commit()
    db.refresh(request)
    return request
