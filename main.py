from datetime import datetime, timedelta, timezone
from typing import Annotated, Union

from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import JWTError, jwt
from passlib.context import CryptContext
from pydantic import BaseModel

# to get a string like this run:
# openssl rand -hex 32
SECRET_KEY = "09d25e094faa6ca2556c818166b7a9563b93f7099f6f0f4caa6cf63b88e8d3e7"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30


fake_users_db = {
    "johndoe": {
        "username": "johndoe",
        "full_name": "John Doe",
        "email": "johndoe@example.com",
        "hashed_password": "$2b$12$EixZaYVK1fsbw1ZfbX3OXePaWxn96p36WQoeG6Lruj3vjPGga31lW",
        "disabled": False,
    }
}


class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    username: Union[str, None] = None


class User(BaseModel):
    username: str
    email: Union[str, None] = None
    full_name: Union[str, None] = None
    disabled: Union[bool, None] = None


class UserInDB(User):
    hashed_password: str


pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

app = FastAPI()


def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password):
    return pwd_context.hash(password)


def get_user(db, username: str):
    if username in db:
        user_dict = db[username]
        return UserInDB(**user_dict)


def authenticate_user(fake_db, username: str, password: str):
    user = get_user(fake_db, username)
    if not user:
        return False
    if not verify_password(password, user.hashed_password):
        return False
    return user


def create_access_token(data: dict, expires_delta: Union[timedelta, None] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


async def get_current_user(token: Annotated[str, Depends(oauth2_scheme)]):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
        token_data = TokenData(username=username)
    except JWTError:
        raise credentials_exception
    user = get_user(fake_users_db, username=token_data.username)
    if user is None:
        raise credentials_exception
    return user


async def get_current_active_user(
    current_user: Annotated[User, Depends(get_current_user)],
):
    if current_user.disabled:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user


@app.post("/token")
async def login_for_access_token(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
) -> Token:
    user = authenticate_user(fake_users_db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    return Token(access_token=access_token, token_type="bearer")


@app.get("/users/me/", response_model=User)
async def read_users_me(
    current_user: Annotated[User, Depends(get_current_active_user)],
):
    return current_user


@app.get("/users/me/items/")
async def read_own_items(
    current_user: Annotated[User, Depends(get_current_active_user)],
):
    return [{"item_id": "Foo", "owner": current_user.username}]









# import datetime
# from typing import Any

# import bcrypt
# import jwt
# from fastapi import Depends, FastAPI, HTTPException, Security, status
# from fastapi.security import OAuth2PasswordBearer, SecurityScopes
# from fastapi.testclient import TestClient
# from pydantic import BaseModel
# from starlette.requests import Request


# fake_users = [
#     # password foo
#     {'id': 1, 'username': 'admin', 'password': 'qwert',
#      'permissions': ['items:read', 'items:write', 'users:read', 'users:write']
#     },
#     # password bar
#     {'id': 2, 'username': 'client', 'password': 'asdf',
#      'permissions': ['items:read']}
# ]

# class UserBase(BaseModel):
#     username: str
#     password: str

# class LoginData(UserBase):
#     pass

# class PyUser(UserBase):
#     id: int
#     permissions: list[str] = []

# class Token(BaseModel):
#     access_token: str
#     token_type: str

# app = FastAPI()

# oauth_scheme = OAuth2PasswordBearer(
#     tokenUrl="token",
#     scopes={'items': 'permissions to access items'}
# )

# def authenticate_user(username: str, password: str) -> PyUser:
#     exception = HTTPException(
#                     status_code=status.HTTP_401_UNAUTHORIZED,
#                     detail='Invalid credentials'
#                 )
#     for obj in fake_users:
#         if obj['username'] == username:
#             # if not bcrypt.checkpw(password.encode(), obj['password'].encode()):
#             #     raise exception
#             user = PyUser(**obj)
#             return user
#     raise exception

# async def get_current_user(request: Request, token: str = Depends(oauth_scheme)):
#     decoded = jwt.decode(token, 'secret', algorithms=['HS256'])
#     username = decoded['sub']
#     for obj in fake_users:
#         if obj['username'] == username:
#             user = PyUser(**obj)
#             # Store the authenticated user in the request context
#             request.state.user = user
#             return user
#     raise HTTPException(
#         status_code=status.HTTP_401_UNAUTHORIZED,
#         detail='Invalid credentials'
#     )

# def create_token(user: PyUser) -> str:
#     payload = {'sub': user.username, 'iat': datetime.datetime.utcnow(),
#                'exp': datetime.datetime.utcnow() + datetime.timedelta(minutes=90)}
#     token = jwt.encode(payload, key='secret')
#     return token

# @app.post('/token')
# def login(login_data: LoginData) -> Token:
#     user = authenticate_user(**login_data.dict())
#     token_str = create_token(user)
#     token = Token(access_token=token_str, token_type='bearer')
#     return token

# @app.get('/users/me')
# def get_user(current_user: PyUser = Depends(get_current_user)):
#     return current_user

# class PermissionChecker:
#     def __init__(self, required_permissions: list[str]) -> None:
#         self.required_permissions = required_permissions

#     def __call__(self, request: Request) -> bool:
#         # Retrieve the authenticated user from the request context
#         current_user = request.state.user
#         for r_perm in self.required_permissions:
#             if r_perm not in current_user.permissions:
#                 raise HTTPException(
#                     status_code=status.HTTP_401_UNAUTHORIZED,
#                     detail='Permissions'
#                 )
#         return True


# @app.get('/items')
# def items(
#     request: Request,
#     authorize: bool = Depends(PermissionChecker(required_permissions=['items:read']))
# ):
#     # Retrieve the authenticated user from the request context
#     current_user = request.state.user
#     return 'items'

# @app.get('/users')
# def users(
#     request: Request,
#     authorize: bool = Depends(PermissionChecker(required_permissions=['users:read']))
# ):
#     # Retrieve the authenticated user from the request context
#     current_user = request.state.user
#     return 'users'







# from fastapi import FastAPI, Depends, HTTPException, status
# from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
# from pydantic import BaseModel
# from datetime import datetime, timedelta
# import jwt

# SECRET_KEY = "your_secret_key"
# ALGORITHM = "HS256"
# ACCESS_TOKEN_EXPIRE_MINUTES = 30

# app = FastAPI()

# oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

# class Token(BaseModel):
#     access_token: str
#     token_type: str

# class TokenData(BaseModel):
#     username: str = None

# class User(BaseModel):
#     username: str
#     email: str = None
#     full_name: str = None
#     disabled: bool = None

# class UserInDB(User):
#     hashed_password: str

# fake_users_db = {
#     "johndoe": {
#         "username": "johndoe",
#         "full_name": "John Doe",
#         "email": "johndoe@example.com",
#         "hashed_password": "$2b$12$EixZaYVK1fsbw1ZfbX3OXePaWxn96p36WQoeG6Lruj3vjPGga31lW",
#         "disabled": False,
#     }
# }

# def get_user(db, username: str):
#     if username in db:
#         user_dict = db[username]
#         return UserInDB(**user_dict)

# def authenticate_user(fake_db, username: str, password: str):
#     user = get_user(fake_db, username)
#     if not user:
#         return False
#     # if not verify_password(password, user.hashed_password):
#     #     return False
#     return user

# def create_access_token(data: dict, expires_delta: timedelta = None):
#     to_encode = data.copy()
#     if expires_delta:
#         expire = datetime.utcnow() + expires_delta
#     else:
#         expire  =  to_encode.update({"exp": expire})
#     encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
#     return encoded_jwt

# async def get_current_user(token: str = Depends(oauth2_scheme)):
#     credentials_exception = HTTPException(
#         status_code=status.HTTP_401_UNAUTHORIZED,
#         detail="Could not validate credentials",
#         headers={"WWW-Authenticate": "Bearer"},
#     )
#     try:
#         payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
#         username: str = payload.get("sub")
#         if username is None:
#             raise credentials_exception
#         token_data = TokenData(username=username)
#     except jwt.PyJWTError:
#         raise credentials_exception
#     user = get_user(fake_users_db, username=token_data.username)
#     if user is None:
#         raise credentials_exception
#     return user

# @app.post("/token", response_model=Token)
# async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
#     user = authenticate_user(fake_users_db, form_data.username, form_data.password)
#     if not user:
#         raise HTTPException(
#             status_code=status.HTTP_401_UNAUTHORIZED,
#             detail="Incorrect username or password",
#             headers={"WWW-Authenticate": "Bearer"},
#         )
#     access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
#     access_token = create_access_token(
#         data={"sub": user.username}, expires_delta=access_token_expires
#     )
#     return {"access_token": access_token, "token_type": "bearer"}

# @app.get("/users/me/", response_model=User)
# async def read_users_me(current_user: User = Depends(get_current_user)):
#     return current_user
