from sqlalchemy import Column, Integer, String, dateTime, foreignKey, text
from sqlalchemy.orm import relationship
from app.database import Base
from sqlalchemy.sql import func


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(100), unique=True, index=True, nullable=False)
    full_name = Column(String(50), nullable=False)
    hashed_password = Column(String(255), nullable=False)
    created_at = Column(dateTime(timezone=True), server_default=func.now())
    updated_at = Column(dateTime(timezone=True), onupdate=func.now())

    documents = relationship("Document", back_populates="owner")


class Document(Base):
    __tablename__ = "documents"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, foreignKey("users.id"))
    doc_type = Column(String, nullable=False)
    filename = Column(String, nullable=False)
    storage_path = Column(String, nullable=False)
    iv = Column(String, nullable=False)
    created_at = Column(dateTime(timezone=True), server_default=func.now())

    owner = relationship("User", back_populates="documents")


class VerificationRequest(Base):
    __tablename__ = "verification_requests"
    id = Column(Integer, primary_key=True, index=True)
    token = Column(String, unique=True, index=True, nullable=False)
    verifier_name = Column(String, nullable=False)
    requested_field = Column(String, nullable=False)
    expire_at = Column(dateTime(timezone=True), nullable=False)
    created_at = Column(dateTime(timezone=True), server_default=func.now())


class AuditLog(Base):
    __tablename__ = "audit_logs"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, foreignKey("users.id"))
    verification_request_id = Column(Integer, nullable=True)
    action = Column(String, nullable=False)
    details = Column(String, nullable=True)
    created_at = Column(dateTime(timezone=True), server_default=func.now())
