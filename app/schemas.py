from pydantic import BaseModel
from typing import Optional, List


class UserBase(BaseModel):
    email: str
    password: str
    full_name: Optional[str] = None


class UserOut(BaseModel):
    id: int
    email: str
    full_name: Optional[str] = None

    class Config:
        orm_mode = True


class tocken(BaseModel):
    access_token: str
    token_type: str = "bearer"


class VerificationRequestBase(BaseModel):
    verifier_name: Optional[str]
    requested_field: Optional[list[str]] = []
