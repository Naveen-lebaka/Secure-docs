# app/main.py
import os
import json
from fastapi import FastAPI, Depends, UploadFile, File, HTTPException, Form
from fastapi.responses import HTMLResponse, StreamingResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session
from . import models, schemas, crud, utils
from .database import SessionLocal, engine
from .auth import get_password_hash, verify_password, create_access_token, get_current_user
from .config import settings
from datetime import timedelta
from fastapi.security import OAuth2PasswordRequestForm

# create tables
models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="Secure Docs (local)")

# Serve static files
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

# ----- Auth (we keep register/login for optional laptop uploads if wanted) -----


@app.post("/api/auth/register")
def register(user: schemas.UserCreate, db: Session = Depends(get_db)):
    existing = crud.get_user_by_email(db, user.email)
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")
    hashed = get_password_hash(user.password)
    u = crud.create_user(db, email=user.email,
                         hashed_password=hashed, full_name=user.full_name)
    return {"id": u.id, "email": u.email, "full_name": u.full_name}


@app.post("/api/auth/login")
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = crud.get_user_by_email(db, email=form_data.username)
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    access_token = create_access_token(data={"sub": user.email}, expires_delta=timedelta(
        minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES))
    return {"access_token": access_token, "token_type": "bearer"}

# ----- Laptop upload (optional; can be used unauthenticated too) -----


@app.post("/api/documents")
def upload_document(doc_type: str = Form(...), file: UploadFile = File(...), db: Session = Depends(get_db)):
    # Note: no auth required for demo simplicity; in prod require auth.
    content = file.file.read()
    if not utils.is_image_clear(content):
        return JSONResponse(status_code=400, content={"detail": "Please upload a clearer / larger image"})
    path = utils.encrypt_and_save_file(content, file.filename)
    doc = crud.create_document_for_verification(
        db, verification_id=None, doc_type=doc_type, filename=file.filename, storage_path=path)
    crud.create_audit(db, user_id=None, verification_id=None,
                      action="uploaded_document_laptop", details={"doc_id": doc.id})
    return {"status": "ok", "doc_id": doc.id}


@app.get("/api/documents")
def list_docs(db: Session = Depends(get_db)):
    docs = db.query(models.Document).all()
    out = [{"id": d.id, "doc_type": d.doc_type, "filename": d.filename,
            "created_at": d.created_at.isoformat()} for d in docs]
    return out

# ----- Create verification request (verifier on laptop) -----


@app.post("/api/verification-requests")
def create_verification(verifier_name: str = Form(None), requested_fields: str = Form("[]"), db: Session = Depends(get_db)):
    req_fields = json.loads(requested_fields)
    vr = crud.create_verification_request(
        db, verifier_name=verifier_name, requested_fields=req_fields)
    qr = utils.generate_qr_base64(settings.BASE_URL + f"/verify/{vr.token}")
    return {"token": vr.token, "qr": qr, "link": settings.BASE_URL + f"/verify/{vr.token}"}

# Desktop verify page


@app.get("/verify/{token}", response_class=HTMLResponse)
def verify_page(token: str, db: Session = Depends(get_db)):
    vr = crud.get_verification_by_token(db, token=token)
    if not vr:
        return HTMLResponse("Invalid token", status_code=404)
    with open("app/static/verify_desktop.html", "r", encoding="utf-8") as f:
        html = f.read().replace("{{TOKEN}}", token)
    return HTMLResponse(html)

# Mobile-friendly verify page (same token)


@app.get("/mobile/verify/{token}", response_class=HTMLResponse)
def mobile_verify_page(token: str, db: Session = Depends(get_db)):
    vr = crud.get_verification_by_token(db, token=token)
    if not vr:
        return HTMLResponse("Invalid token", status_code=404)
    # serve mobile-friendly page
    with open("app/static/verify_mobile.html", "r", encoding="utf-8") as f:
        html = f.read().replace("{{TOKEN}}", token)
    return HTMLResponse(html)

# API: fetch verification meta


@app.get("/api/verify/{token}")
def get_verify_request(token: str, db: Session = Depends(get_db)):
    vr = crud.get_verification_by_token(db, token=token)
    if not vr:
        raise HTTPException(status_code=404, detail="Invalid token")
    return {"token": vr.token, "verifier_name": vr.verifier_name, "requested_fields": json.loads(vr.requested_fields)}

# ----- PUBLIC mobile upload endpoint for token (no JWT) -----


@app.post("/api/verify/{token}/upload")
def mobile_upload(token: str, doc_type: str = Form(...), file: UploadFile = File(...), db: Session = Depends(get_db)):
    vr = crud.get_verification_by_token(db, token=token)
    if not vr:
        raise HTTPException(status_code=404, detail="Invalid token")
    content = file.file.read()
    # clarity check
    if not utils.is_image_clear(content):
        return JSONResponse(status_code=400, content={"detail": "Please upload a clearer / larger image"})
    path = utils.encrypt_and_save_file(content, file.filename)
    doc = crud.create_document_for_verification(
        db, verification_id=vr.id, doc_type=doc_type, filename=file.filename, storage_path=path)
    crud.create_audit(db, user_id=None, verification_id=vr.id, action="mobile_uploaded", details={
                      "doc_id": doc.id, "doc_type": doc_type})
    return {"status": "ok", "doc_id": doc.id}

# List uploaded docs for a token (for verifier to see)


@app.get("/api/verification/{token}/documents")
def list_verification_docs(token: str, db: Session = Depends(get_db)):
    vr = crud.get_verification_by_token(db, token=token)
    if not vr:
        raise HTTPException(status_code=404, detail="Invalid token")
    docs = crud.list_documents_for_verification(db, vr.id)
    out = [{"id": d.id, "doc_type": d.doc_type, "filename": d.filename,
            "created_at": d.created_at.isoformat()} for d in docs]
    return out

# Verifier download (no JWT but requires doc tied to token and that doc exists)


@app.get("/api/verification/{token}/download/{doc_id}")
def verifier_download(token: str, doc_id: int, db: Session = Depends(get_db)):
    vr = crud.get_verification_by_token(db, token=token)
    if not vr:
        raise HTTPException(status_code=404, detail="Invalid token")
    doc = db.query(models.Document).filter(models.Document.id == doc_id,
                                           models.Document.verification_request_id == vr.id).first()
    if not doc:
        raise HTTPException(
            status_code=403, detail="This document is not available for this verification request")
    data = utils.decrypt_file_to_bytes(doc.storage_path)
    crud.create_audit(db, user_id=None, verification_id=vr.id,
                      action="verifier_downloaded", details={"doc_id": doc_id})
    return StreamingResponse(iter([data]), media_type="application/octet-stream", headers={"Content-Disposition": f"attachment; filename={doc.filename}"})
