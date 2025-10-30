# app/crud.py
import uuid
import os
from sqlalchemy.orm import Session
from app import models
from app.database import UPLOAD_DIR


def create_upload_session(db: Session, verifier_name: str | None = None) -> models.UploadSession:
    session_id = str(uuid.uuid4())
    s = models.UploadSession(id=session_id, verifier_name=verifier_name)
    db.add(s)
    db.commit()
    db.refresh(s)
    # ensure folder exists
    os.makedirs(os.path.join(UPLOAD_DIR, session_id), exist_ok=True)
    return s


def get_upload_session(db: Session, session_id: str):
    return db.get(models.UploadSession, session_id)


def record_document_upload(db: Session, session_id: str, doc_type: str, filename: str, filepath: str, content_type: str):
    du = models.DocumentUpload(session_id=session_id, doc_type=doc_type,
                               filename=filename, filepath=filepath, content_type=content_type)
    db.add(du)
    db.commit()
    db.refresh(du)
    return du


def list_uploads_for_session(db: Session, session_id: str):
    q = db.query(models.DocumentUpload).filter(
        models.DocumentUpload.session_id == session_id).all()
    return q
