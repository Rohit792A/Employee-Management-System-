# from fastapi import Depends, FastAPI, HTTPException, status
# from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
# from pydantic import BaseModel
# from datetime import datetime, timedelta
# import jwt
# from passlib.context import CryptContext
from fastapi import FastAPI, Depends, HTTPException
from models import User as newuser
from Schema import User
from database import get_db
from sqlalchemy.orm import Session
from pydantic import BaseModel
from fastapi.security import OAuth2PasswordRequestForm,OAuth2PasswordBearer
import jwt
from datetime import datetime, timedelta
from passlib.context import CryptContext


SECRET_KEY = "83daa0256a2289b0fb23693bf1f6034d44396675749244721a2b20e896e11662"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

db = {
    "tim": {
        "username": "tim",
        "full_name": "Tim Ruscica",
        "email": "tim@gmail.com",
        "hashed_password": "$2b$12$HxWHkvMuL7WrZad6lcCfluNFj1/Zp63lvP5aUrKlSTYtoFzPXHOtu",
        "disabled": False
    }
}


class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    username: str


class User(BaseModel):
    username: str
    email: str
    full_name: str 
    disabled: bool 


class UserInDB(User):
    hashed_password: str


pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

app = FastAPI()


def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password):
    return pwd_context.hash(password)


def get_user(username: str,db: Session = Depends(get_db) ):
    return db.query(newuser).filter(newuser.name == username).first()

    
    if username in db:
        user_data = db[username]
        return UserInDB(**user_data)


def authenticate_user(db, username: str, password: str):
    user = get_user(db, username)
    if not user:
        return False
    if not verify_password(password, user.hashed_password):
        return False

    return user


def create_access_token(data: dict, expires_delta: timedelta or None = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)

    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


async def get_current_user(token: str = Depends(oauth2_scheme)):
    credential_exception = HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                                         detail="Could not validate credentials", headers={"WWW-Authenticate": "Bearer"})
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credential_exception

        token_data = TokenData(username=username)
    except jwt.PyJWTError:
        raise credential_exception

    user = get_user(db, username=token_data.username)
    if user is None:
        raise credential_exception

    return user


async def get_current_active_user(current_user: UserInDB = Depends(get_current_user)):
    if current_user.disabled:
        raise HTTPException(status_code=400, detail="Inactive user")

    return current_user


@app.post("/token", response_model=Token)
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
    user = authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                            detail="Incorrect username or password", headers={"WWW-Authenticate": "Bearer"})
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires)
    return {"access_token": access_token, "token_type": "bearer"}


@app.get("/users/me/", response_model=User)
async def read_users_me(current_user: User = Depends(get_current_active_user)):
    return current_user


@app.get("/users/me/items")
async def read_own_items(current_user: User = Depends(get_current_active_user)):
    return [{"item_id": 1, "owner": current_user}]








































# from fastapi import FastAPI, Depends, HTTPException
# from models import User
# from database import get_db
# from pydantic import BaseModel
# from fastapi.security import OAuth2PasswordRequestForm,OAuth2PasswordBearer
# import jwt
# from datetime import datetime, timedelta
# from passlib.context import CryptContext

# app = FastAPI()

# # Replace with your actual user database or user store
# USERS = get_db

# SECRET_KEY = "mykey"  # Replace with a secure secret key
# ALGORITHM = "HS256"
# ACCESS_TOKEN_EXPIRE_MINUTES = 30

# bcrypt_context = CryptContext(schemes=['bcrypt'], deprecated="auto")

# oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")



# class CreateUserRequest(BaseModel):
#     username: str
#     password: str

# class Token(BaseModel):
#     access_token: str
#     token_type: str







# def authenticate_user(name: str, password: str):
#     user = USERS.get(User,name)
#     if not user or user["password"] != password:
#         return False
#     return user

# def create_access_token(data: dict, expires_delta: timedelta = None):
#     to_encode = data.copy()
#     if expires_delta:
#         expire = datetime.now() + expires_delta
#     else:
#         expire = datetime.now() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
#     to_encode.update({"exp": expire})
#     encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
#     return encoded_jwt


# async def get_current_user(token: str = Depends(oauth2_scheme)):
#     try:
#         payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
#         username: str = payload.get("sub")
#         user_id: int = payload.get("user_id")
#         if username is None or user_id is None:
#             raise HTTPException(
#                 status_code=status.HTTP_401_UNAUTHORIZED,
#                 detail="Could not validate user credentials",
#             )
#         return {"username": username, "id": user_id}
#     except jwt.PyJWTError:
#         raise HTTPException(
#             status_code=status.HTTP_401_UNAUTHORIZED,
#             detail="Could not validate user credentials",
#         )

# @app.post("/token")
# async def login(form_data: OAuth2PasswordRequestForm = Depends()):
#     user = authenticate_user(form_data.username, form_data.password)
#     if not user:
#         raise HTTPException(status_code=400, detail="Incorrect username or password")
#     access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
#     access_token = create_access_token(
#         data={"user_type": user["user_type"]}, expires_delta=access_token_expires
#     )
#     return {"access_token": access_token, "token_type": "bearer"}



# # Other routes that require authentication
# @app.get("/protected")
# async def protected_route(user_type: str = Depends(authenticate_user)):
#     return {"message": f"Hello, {user_type}!"}


























# from fastapi import Depends, HTTPException, status
# from fastapi.security import OAuth2PasswordBearer
# import jwt

# oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

# SECRET_KEY = "secret_key"  # Replace with a secure secret key

# def get_current_user(token: str):
#     try:
#         payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
#         user_type = payload.get("user_type")
#         if user_type is None:
#             raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
#         return user_type
#     except jwt.PyJWTError:
#         raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")

# def authenticate_user(user_type: str = None):
#     def _authenticate(token: str = Depends(oauth2_scheme)):
#         current_user_type = get_current_user(token)
#         if user_type and current_user_type != user_type:
#             raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Unauthorized user type")
#         return current_user_type
#     return _authenticate
