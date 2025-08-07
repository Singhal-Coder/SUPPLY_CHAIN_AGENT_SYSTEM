# server/utils/db.py
import os
from sqlalchemy import create_engine
from dotenv import load_dotenv

load_dotenv()

def get_db_engine():
    """
    Creates and returns a SQLAlchemy engine using the DATABASE_URL.
    """
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        raise ValueError("DATABASE_URL not found in environment variables.")
    
    engine = create_engine(database_url)
    return engine