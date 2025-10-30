# app/database.py
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from dotenv import load_dotenv

load_dotenv()

MYSQL_USER = os.getenv("MYSQL_USER", "root")
MYSQL_PASSWORD = os.getenv("MYSQL_PASSWORD", "root123")
MYSQL_HOST = os.getenv("MYSQL_HOST", "127.0.0.1")
MYSQL_PORT = os.getenv("MYSQL_PORT", "3306")
MYSQL_DB = os.getenv("MYSQL_DB", "secure_docs_db")
UPLOAD_DIR = os.getenv("UPLOAD_DIR", "./uploads")

DATABASE_URL = (
    f"mysql+pymysql://{MYSQL_USER}:{MYSQL_PASSWORD}@{MYSQL_HOST}:{MYSQL_PORT}/{MYSQL_DB}?charset=utf8mb4"
)

# ✅ Updated engine with proper pool management
engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,     # keeps connection alive
    pool_size=10,           # base pool size (default 5)
    max_overflow=20,        # temporary connections beyond pool_size
    pool_timeout=60,        # wait 60 seconds before raising TimeoutError
    pool_recycle=1800,      # recycle every 30 minutes to avoid stale MySQL conns
    future=True,
)

# ✅ Session maker
SessionLocal = sessionmaker(
    autocommit=False, autoflush=False, bind=engine, future=True)
Base = declarative_base()

# ✅ Ensure DB tables are created


def init_db():
    from app import models
    Base.metadata.create_all(bind=engine)

# ✅ Critical: Proper DB dependency for FastAPI


def get_db():
    """Dependency for FastAPI routes that auto-closes DB sessions."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
