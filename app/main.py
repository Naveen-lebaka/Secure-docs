import os
import json
from fastapi import FastAPI, Depends, UploadFile, File, HTTPException, Form
from fastapi.responses import HTMLResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session
from . import models, schemas, crud, utils
from .database import SessionLocal, engine
from .auth import get_password_hash, verify_password, create_access_token, get_current_user
from .config import settings
from datetime import timedelta
from fastapi.security import OAuth2PasswordRequestForm

models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="Secure Docs (local)")

# Serve static simple HTML
app.mount("/static", StaticFiles(directory="app/static"), name="static")


def get_db():
    try:
        db = SessionLocal()
        yield db
    finally:
        db.close()


@app.get("/", response_class=HTMLResponse)
def index():
    with open("app/static/index.html", "r", encoding="utf-8") as f:
        return HTMLResponse(f.read())

# ----- Auth -----


@app.post("/api/auth/register", response_model=schemas.UserOut)
def register(user: schemas.UserCreate, db: Session = Depends(get_db)):
    existing = crud.get_user_by_email(db, user.email)
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")
    hashed = get_password_hash(user.password)
    u = crud.create_user(db, email=user.email,
                         hashed_password=hashed, full_name=user.full_name)
    return u


@app.post("/api/auth/login", response_model=schemas.Token)
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = crud.get_user_by_email(db, email=form_data.username)
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    access_token = create_access_token(data={"sub": user.email}, expires_delta=timedelta(
        minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES))
    return {"access_token": access_token, "token_type": "bearer"}

# ----- Upload document -----


@app.post("/api/documents")
def upload_document(doc_type: str = Form(...), file: UploadFile = File(...), current_user=Depends(get_current_user), db: Session = Depends(get_db)):
    content = file.file.read()
    path = utils.encrypt_and_save_file(content, file.filename)
    doc = crud.create_document(db, user_id=current_user.id,
                               doc_type=doc_type, filename=file.filename, storage_path=path)
    crud.create_audit(db, user_id=current_user.id, verification_id=None,
                      action="uploaded_document", details={"doc_id": doc.id, "filename": file.filename})
    return {"status": "ok", "doc_id": doc.id}

# List user's documents


@app.get("/api/documents")
def list_docs(current_user=Depends(get_current_user), db: Session = Depends(get_db)):
    docs = crud.list_documents_for_user(db, current_user.id)
    out = [{"id": d.id, "doc_type": d.doc_type, "filename": d.filename,
            "created_at": d.created_at.isoformat()} for d in docs]
    return out

# Download decrypted file (only for authorized)


@app.get("/api/documents/{doc_id}/download")
def download_doc(doc_id: int, current_user=Depends(get_current_user), db: Session = Depends(get_db)):
    doc = db.query(models.Document).filter(
        models.Document.id == doc_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Doc not found")
    if doc.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not allowed")
    data = utils.decrypt_file_to_bytes(doc.storage_path)
    return StreamingResponse(iter([data]), media_type="application/octet-stream", headers={"Content-Disposition": f"attachment; filename={doc.filename}"})

# ----- Verification request creation (by verifier) -----


@app.post("/api/verification-requests")
def create_verification(verifier_name: str = Form(None), requested_fields: str = Form("[]"), db: Session = Depends(get_db)):
    req_fields = json.loads(requested_fields)
    vr = crud.create_verification_request(
        db, verifier_name=verifier_name, requested_fields=req_fields)
    qr = utils.generate_qr_base64(settings.BASE_URL + f"/verify/{vr.token}")
    return {"token": vr.token, "qr": qr, "link": settings.BASE_URL + f"/verify/{vr.token}"}

# Simple verify page


@app.get("/verify/{token}", response_class=HTMLResponse)
def verify_page(token: str, db: Session = Depends(get_db)):
    vr = crud.get_verification_by_token(db, token=token)
    if not vr:
        return HTMLResponse("Invalid token", status_code=404)
    with open("app/static/verify.html", "r", encoding="utf-8") as f:
        html = f.read().replace("{{TOKEN}}", token)
    return HTMLResponse(html)

# Endpoint the verify page calls to get requested fields


@app.get("/api/verify/{token}")
def get_verify_request(token: str, db: Session = Depends(get_db)):
    vr = crud.get_verification_by_token(db, token=token)
    if not vr:
        raise HTTPException(status_code=404, detail="Invalid token")
    return {"token": vr.token, "verifier_name": vr.verifier_name, "requested_fields": json.loads(vr.requested_fields)}

# User shares document via the verify page; this requires auth (token)


@app.post("/api/verify/{token}/share")
def share_document(token: str, doc_id: int = Form(...), current_user=Depends(get_current_user), db: Session = Depends(get_db)):
    vr = crud.get_verification_by_token(db, token=token)
    if not vr:
        raise HTTPException(status_code=404, detail="Invalid token")
    doc = db.query(models.Document).filter(
        models.Document.id == doc_id).first()
    if not doc or doc.user_id != current_user.id:
        raise HTTPException(
            status_code=403, detail="Not allowed to share this doc")
    # record audit
    crud.create_audit(db, user_id=current_user.id, verification_id=vr.id,
                      action="user_shared", details={"doc_id": doc.id, "filename": doc.filename})
    # for simplicity: return a download link that the verifier can use (in real prod use pre-signed S3 URL)
    download_link = settings.BASE_URL + \
        f"/api/verification/{token}/download/{doc.id}"
    return {"shared": True, "download_link": download_link}

# Verifier downloads (no auth) but must have token and doc_id, and we verify token/audit


@app.get("/api/verification/{token}/download/{doc_id}")
def verifier_download(token: str, doc_id: int, db: Session = Depends(get_db)):
    vr = crud.get_verification_by_token(db, token=token)
    if not vr:
        raise HTTPException(status_code=404, detail="Invalid token")
    # check audit log that user shared this doc for this verification request
    logs = db.query(models.AuditLog).filter(models.AuditLog.verification_request_id ==
                                            vr.id, models.AuditLog.action == "user_shared").all()
    allowed_doc_ids = []
    for l in logs:
        try:
            detail = json.loads(l.details)
            if detail.get("doc_id"):
                allowed_doc_ids.append(int(detail.get("doc_id")))
        except:
            pass
    if doc_id not in allowed_doc_ids:
        raise HTTPException(
            status_code=403, detail="This document was not shared for this request")
    doc = db.query(models.Document).filter(
        models.Document.id == doc_id).first()
    data = utils.decrypt_file_to_bytes(doc.storage_path)
    crud.create_audit(db, user_id=None, verification_id=vr.id,
                      action="verifier_downloaded", details={"doc_id": doc_id})
    return StreamingResponse(iter([data]), media_type="application/octet-stream", headers={"Content-Disposition": f"attachment; filename={doc.filename}"})
