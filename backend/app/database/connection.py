import os
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# Default database is SQLite in the backend folder
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./insightai.db")

# Create engine. For SQLite, allow multi-threaded access.
connect_args = {}
if DATABASE_URL.startswith("sqlite"):
    connect_args["check_same_thread"] = False

engine = create_engine(DATABASE_URL, connect_args=connect_args)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

# Dependency to get db session in FastAPI route handlers
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
