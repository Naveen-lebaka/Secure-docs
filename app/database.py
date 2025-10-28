# app/database.py
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import urllib.parse

MYSQL_USER = "root"                    # replace with your user
MYSQL_PASSWORD = "root123"  # replace with your password
MYSQL_HOST = "localhost"
MYSQL_PORT = "3306"
MYSQL_DB = "secure_docs_db"

# URL encode password if it has special characters
encoded_password = urllib.parse.quote_plus(MYSQL_PASSWORD)

SQLALCHEMY_DATABASE_URL = (
    f"mysql+pymysql://{MYSQL_USER}:{encoded_password}@{MYSQL_HOST}:{MYSQL_PORT}/{MYSQL_DB}"
)

engine = create_engine(SQLALCHEMY_DATABASE_URL, future=True)
SessionLocal = sessionmaker(
    autocommit=False, autoflush=False, bind=engine, future=True)
Base = declarative_base()
