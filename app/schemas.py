from pydantic import BaseModel
from typing import Optional, List


class UserCreate(BaseModel):
    email: str
    password: str
    full_name: Optional[str] = None


class UserOut(BaseModel):
    id: int
    email: str
    full_name: Optional[str]

    class Config:
        orm_mode = True


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class VerificationCreate(BaseModel):
    verifier_name: Optional[str]
    requested_fields: Optional[List[str]] = []
