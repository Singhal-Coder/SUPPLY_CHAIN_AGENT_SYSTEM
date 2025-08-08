# server/utils/db.py
import os
from sqlalchemy import create_engine
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    raise ValueError("DATABASE_URL not found in environment variables.")

engine = create_engine(DATABASE_URL)

def get_db_engine():
    """
    Returns the shared SQLAlchemy engine instance.
    """
    return engine