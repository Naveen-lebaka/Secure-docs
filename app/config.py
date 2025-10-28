from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    SECRET_KEY: str = "Naveen"
    FERNET_KEY: str = ""
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    # change to laptop IP when testing on phone
    BASE_URL: str = "http://127.0.0.1:8000"

    class Config:
        env_file = ".env"


settings = Settings()
