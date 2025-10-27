from pydantic import BaseSettings


class Settings(BaseSettings):
    SECRETE_KEY: str = "Naveen@123"
    fernet_key: str = ""
    access_token_expire_minutes: int = 60
    base_url: str = "http://127.0.0.1:8000"

    class Config:
        env_file = "../.env"


settings = Settings()
