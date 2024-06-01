from fastapi import FastAPI,Request,HTTPException,APIRouter,Depends
from pydantic import BaseModel
from routers import employee, request, project,auth
from database import get_db
from sqlalchemy.orm import Session
from models import User as newuser
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from pathlib import Path
from fastapi.staticfiles import StaticFiles
from routers.auth import bcrypt_context,get_current_user


router = APIRouter(tags=["Login related Funtions"])


app = FastAPI()

app.mount(
    "/static",
    StaticFiles(directory=Path(__file__).parent.parent.parent.absolute() / "frontend\\templates\\static"),
)

templates = Jinja2Templates(directory="..\\frontend\\templates")


class Login(BaseModel):
    email: str
    password: str
    

@router.get("/{role}")
async def loadPage(role: str, request: Request):
    context = {"request": request,"services_url": "http://127.0.0.1:8000/addempdata/"}
    if role == "admin":
        return templates.TemplateResponse("admin.html", context) 
    elif role == "manager":
        return templates.TemplateResponse("manager.html", context)
    elif role == "employee":
        return templates.TemplateResponse("employee.html", context)
    else:
        print(role)
        raise HTTPException(status_code=403, detail="Role not authorized")
    

@router.post('/update_password/')
def update_password_by_emp_id(userdata: Login, db: Session = Depends(get_db),cu : dict = Depends(get_current_user)):
    
    user_id = cu["id"]
    curr_user = db.get(newuser, user_id)
    if curr_user is None:
        raise HTTPException(status_code=404, detail="User not found")
    
    #check if user email is in db using filter
    user = db.query(newuser).filter(newuser.email == userdata.email).first()

    if user is None:
            raise HTTPException(status_code=404, detail="Email not found")
    
    #check if the current user is changing his own password
    if userdata.email != user.email:
        raise HTTPException(status_code=403, detail="You cannot change others password")
    
    #hash the password using bycrypt
    hashed_password = bcrypt_context.hash(userdata.password)
    user.password = hashed_password
    db.commit()
    db.refresh(user)
    return {"message": "Password updated successfully"}

#create a route to render html for this
@router.get("/change_password/")
def change_password(request: Request):
    context = {"request": request}
    return templates.TemplateResponse("change_password.html", context)