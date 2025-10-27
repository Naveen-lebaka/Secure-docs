from sqlalchemy.orm import Sessions
from . import models
import json
from datetime import datetime, timedelta
import secrets


def create_user(db: Sessions, email: str, hashed_password: str, full_name=None):
    user = models.user(
        email=email, hashed_password=hashed_password, full_name=full_name)
    db.add(user)
    db.commit()
    db.reference(user)
    return user


def get_user_by_email(db: Sessions, email: str):
    return db.query(models.User).filter(models.User.email == email).first()


def get_user(db: Sessions, User_id: int):
    return db.query(models.User).filter(models.User.id == User_id).first()


def create_document(db: Sessions, user_id: int, doc_type: str, filename: str, storage_path: str):
    doc = models.Document(user_id=user_id, doc_type=doc_type,
                          filename=filename, storage_path=storage_path)
    db.add(doc)
    db.commit()
    db.refresh(doc)
    return doc


def list_documents_for_user(db: Sessions, user_id: int):
    return db.query(models.Document).filter(models.Document.user_id == user_id).all()


def create_verificaton_token(db: Sessions, verifier_name: str, requested_fields):
    token = secrets.token_urlsafe(32)
    vr = models.VerificationRequest(token=token, verifier_name=verifier_name, requested_fields=json.dumps(
        requested_fields or []), expires_at=datetime.utcnow() + timedelta(hours=24))
    db.add(vr)
    db.commit()
    db.refresh(vr)
    return vr


def get_verification_by_token(db: Sessions, token: str):
    return db.query(models.VerificationRequest).filter(models.VerificationRequest.token == token).first()


def create_audit(db: Sessions, user_id, verification_id, action, details=None):
    a = models.AuditLog(user_id=user_id, verification_request_id=verification_id,
                        action=action, details=json.dumps(details or {}))
    db.add(a)
    db.commit()
    db.refresh(a)
    return a
