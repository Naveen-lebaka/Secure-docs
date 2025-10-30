# app/models.py
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text
from sqlalchemy.sql import func
from app.database import Base
from sqlalchemy.orm import relationship


class UploadSession(Base):
    __tablename__ = "upload_sessions"
    id = Column(String(36), primary_key=True)  # uuid string
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    status = Column(String(20), default="open")  # open / completed
    verifier_name = Column(String(128), nullable=True)

    uploads = relationship("DocumentUpload", back_populates="session")


class DocumentUpload(Base):
    __tablename__ = "document_uploads"
    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String(36), ForeignKey("upload_sessions.id"))
    doc_type = Column(String(64))  # e.g., 'aadhaar', 'passport'
    filename = Column(String(256))
    filepath = Column(String(512))
    content_type = Column(String(64))
    uploaded_at = Column(DateTime(timezone=True), server_default=func.now())
    notes = Column(Text, nullable=True)

    session = relationship("UploadSession", back_populates="uploads")
