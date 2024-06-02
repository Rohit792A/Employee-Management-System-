from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy.ext.declarative import declarative_base

DATABASE_URL = "postgresql://postgres:rohit792A@localhost:5432/EMS_Database"

# Create an engine object to connect to the PostgreSQL database
engine = create_engine(DATABASE_URL)

# Create a sessionmaker object to create database sessions
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Define the base class for all SQLAlchemy ORM models
Base = declarative_base()

# Create the database tables using the Base.metadata.create_all() method
Base.metadata.create_all(bind=engine)

# Define a function to create a new database session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()