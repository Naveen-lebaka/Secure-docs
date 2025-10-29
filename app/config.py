# app/config.py
import os
from dotenv import load_dotenv

load_dotenv(dotenv_path=os.path.join(
    os.path.dirname(os.path.dirname(__file__)), ".env"))


class Settings:
    SECRET_KEY: str = os.getenv("SECRET_KEY", "changeme")
    FERNET_KEY: str = os.getenv("FERNET_KEY", "")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = int(
        os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "60"))
    BASE_URL: str = os.getenv("BASE_URL", "http://127.0.0.1:8000")

    # MySQL settings
    MYSQL_USER: str = os.getenv("MYSQL_USER", "root")
    MYSQL_PASSWORD: str = os.getenv("MYSQL_PASSWORD", "")
    MYSQL_HOST: str = os.getenv("MYSQL_HOST", "127.0.0.1")
    MYSQL_PORT: int = int(os.getenv("MYSQL_PORT", "3306"))
    MYSQL_DB: str = os.getenv("MYSQL_DB", "secure_docs_db")


settings = Settings()
