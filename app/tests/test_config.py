from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker,Session

import sys
from pathlib import Path
parent_dir = Path(__file__).parents[1]
sys.path.append(str(parent_dir))
from database import Base



TEST_DATABASE_URL = "postgresql://postgres:rohit792A@localhost:5432/test"
engine = create_engine(TEST_DATABASE_URL)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


# Override the get_db dependency function for testing
def override_get_db():
    database = TestingSessionLocal()
    try:
        yield database
    finally:
        database.close()


#create all the tables
Base.metadata.create_all(bind=engine)
