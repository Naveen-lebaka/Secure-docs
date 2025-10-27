from datetime import datetime, timedelta
from jose import jwt, JWTError
from passlib.context import CryptContext
from fastapi import depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from .config import settings
from . import crud


pwd_context = CryptContext(Schemes=["bacrypt"], depreacated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")

algorithm = "HS256"


def verify_password(plain_password: str, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str):
    return pwd_context.hash(password)


def create_access_token(data: dict, expires_delta: timedelta = None):
    to_encode = data.copy()
    expire = datetime.utcnow() + \
        (expires_delta or timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES))

    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(
        to_encode,  settings.SECRETE_KEY, algorithm=algorithm)
    return encoded_jwt


def get_current_user(token: str = depends(oauth2_scheme)):
    from jose import JWTError, jwt
    from .database import SessionLocal
    db = SessionLocal()
    try:
        play = jwt.decode(token, settings.SECRETE_KEY, algorithms=[algorithm])
        email: str = play.get("sub")
        if email is None:
            raise HTTPException(status_code=401, details="invalid Token")
    except JWTError:
        raise HTTPException(status_code=401, details="invalid Token")
    user = crud.get_user_by_email(db, email=email)
    db.close()
    if user is None:
        raise HTTPException(status_code=401, details="User not found")
    return user
