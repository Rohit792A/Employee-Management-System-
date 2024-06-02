import pytest
from fastapi.testclient import TestClient

import sys
from pathlib import Path
parent_dir = Path(__file__).parents[1]
sys.path.append(str(parent_dir))

from run import app
from routers.auth import authenticate_user, create_access_token
from tests.test_config import override_get_db
from models import User
from passlib.context import CryptContext
from datetime import timedelta
from database import get_db



app.dependency_overrides[get_db] = override_get_db

#to clear the db after test
def cleanup_db(db):
    db.query(User).filter(User.email != 'ro@gmail.com').delete()
    db.commit()


# Create a test client
client = TestClient(app)

bcrypt_context = CryptContext(schemes=['bcrypt'], deprecated="auto")


def test_authenticate_user():
    db = next(override_get_db())
    username = "testuser"
    email = "te@gmail.com"
    password = "testpassword"
    user = User(name=username, email=email, password=bcrypt_context.hash(password), user_type="employee")
    db.add(user)
    db.commit()        
    # Correct credentials
    assert authenticate_user(email, password, db) is not False

    # Incorrect credentials
    assert authenticate_user(username, "wrongpassword", db) is False
    assert authenticate_user("wrongusername", password, db) is False
    cleanup_db(db)


def test_create_access_token():
    username = "testuser"
    user_id = 4
    user_role = "admin"
    expires_delta = timedelta(minutes=30)

    token = create_access_token(username, user_id, user_role, expires_delta)
    assert isinstance(token, str)
    assert len(token) > 0


