from fastapi import FastAPI,Request,HTTPException,APIRouter,Depends
from pydantic import BaseModel
from database import get_db
from sqlalchemy.orm import Session
from models import User as newuser
from fastapi.templating import Jinja2Templates
from routers.auth import bcrypt_context,get_current_user


router = APIRouter(tags=["Login related Funtions"])

templates = Jinja2Templates(directory="..\\frontend\\templates")


class Login(BaseModel):
    email: str
    password: str
    
# Render the pages based on the role of the current user
@router.get("/{role}")
async def loadPage(role: str, request: Request):
    context = {"request": request}
    if role == "admin":
        return templates.TemplateResponse("admin.html", context) 
    elif role == "manager":
        return templates.TemplateResponse("manager.html", context)
    elif role == "employee":
        return templates.TemplateResponse("employee.html", context)
    else:
        print(role)
        raise HTTPException(status_code=403, detail="Role not authorized")
    
#  Function to update the password
@router.post('/update_password/')
def update_password_by_emp_id(userdata: Login, db: Session = Depends(get_db),cu : dict = Depends(get_current_user)):
    
    # check if current user is in db
    user_id = cu["id"]
    curr_user = db.get(newuser, user_id)

    # if user is not present raise error
    if curr_user is None:
        raise HTTPException(status_code=404, detail="User not found")
    
    # check if user email is in db using filter
    user = db.query(newuser).filter(newuser.email == userdata.email).first()

    if user is None:
            raise HTTPException(status_code=404, detail="Email not found")
    
    # check if the current user is changing his own password
    if userdata.email != user.email:
        raise HTTPException(status_code=403, detail="You cannot change others password")
    
    # hash the password using bycrypt
    hashed_password = bcrypt_context.hash(userdata.password)
    user.password = hashed_password
    db.commit()
    db.refresh(user)
    return {"message": "Password updated successfully"}

# Function to render html for update password
@router.get("/change_password/")
def change_password(request: Request):
    context = {"request": request}
    return templates.TemplateResponse("change_password.html", context)

# Function to render html for forget password
@router.get("/forget_password/")
def change_password(request: Request):
    context = {"request": request}
    return templates.TemplateResponse("forget_password.html", context)