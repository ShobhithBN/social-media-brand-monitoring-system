import os
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv
import logging

# Load environment variables
load_dotenv()

# Database connection details (allow override via env)
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "5432")
DB_NAME = os.getenv("DB_NAME", "social_media_monitor")
DB_USER = os.getenv("DB_USER", "postgres")
DB_PASSWORD = os.getenv("DB_PASSWORD", "")

# If running inside a Docker container and host still set to localhost, assume service name 'db'
try:
    if os.path.exists("/.dockerenv") and DB_HOST in {"localhost", "127.0.0.1"}:
        DB_HOST = "db"
except Exception:
    pass

# Create SQLAlchemy engine (echo can be toggled with DB_ECHO=1)
ECHO = os.getenv("DB_ECHO", "0") == "1"
DATABASE_URL = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
logging.getLogger(__name__).info(f"Using DATABASE_URL host={DB_HOST} port={DB_PORT} db={DB_NAME}")
engine = create_engine(DATABASE_URL, echo=ECHO, pool_pre_ping=True)

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class for models
Base = declarative_base()

def get_db():
    """Get database session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()