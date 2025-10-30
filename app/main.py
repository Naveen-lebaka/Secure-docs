# app/main.py
import os
import io
from fastapi import FastAPI, Request, UploadFile, File, HTTPException, Depends
from fastapi.responses import HTMLResponse, JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from dotenv import load_dotenv
from PIL import Image

from app import database, crud, utils
from app.database import init_db, UPLOAD_DIR, get_db

# Load environment variables
load_dotenv()

BASE_URL = os.getenv("BASE_URL", "http://192.168.0.103:8000")

# Initialize FastAPI app
app = FastAPI(title="Secure Docs Upload API")

# Mount static and templates
app.mount(
    "/static",
    StaticFiles(directory=os.path.join(os.path.dirname(__file__), "static")),
    name="static",
)
templates = Jinja2Templates(
    directory=os.path.join(os.path.dirname(__file__), "templates")
)

# Ensure DB tables exist at startup
init_db()


# ---------------------------
#          ROUTES
# ---------------------------

@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    """Render the home page."""
    return templates.TemplateResponse("index.html", {"request": request})


@app.post("/create_session")
async def create_session_endpoint(
    payload: dict,
    request: Request,
    db: Session = Depends(get_db),
):
    """Create a new upload session and return QR data."""
    verifier_name = payload.get("verifier_name") if payload else None
    s = crud.create_upload_session(db, verifier_name=verifier_name)

    link = f"{BASE_URL}/upload/{s.id}"
    qr_dataurl = utils.generate_qr_dataurl(link)

    return {"session_id": s.id, "qr_dataurl": qr_dataurl, "link": link}


@app.get("/upload/{session_id}", response_class=HTMLResponse)
async def upload_mobile_page(
    request: Request,
    session_id: str,
    db: Session = Depends(get_db),
):
    """Render mobile upload page for the session."""
    s = crud.get_upload_session(db, session_id)
    if not s:
        raise HTTPException(status_code=404, detail="Session not found")

    return templates.TemplateResponse(
        "upload_mobile.html", {"request": request, "session_id": session_id}
    )


@app.post("/upload_file/{session_id}")
async def upload_file(
    session_id: str,
    file: UploadFile = File(...),
    doc_type: str = None,
    db: Session = Depends(get_db),
):
    """Handle file upload and validation."""
    s = crud.get_upload_session(db, session_id)
    if not s:
        raise HTTPException(
            status_code=404, detail="Session expired or not found")

    # Read and validate file
    contents = await file.read()
    if len(contents) > (8 * 1024 * 1024):  # 8 MB limit
        raise HTTPException(
            status_code=400, detail="File too large. Please use <8MB")

    content_type = file.content_type or ""
    if content_type.startswith("image/"):
        try:
            img = Image.open(io.BytesIO(contents))
            w, h = img.size
            if w < 500 or h < 400:
                raise HTTPException(
                    status_code=400,
                    detail="Image too small/unclear. Please capture a clearer photo",
                )
        except Exception:
            raise HTTPException(status_code=400, detail="Invalid image file")

    # Save file locally
    local_path = utils.save_upload_file(
        session_id, file.filename, io.BytesIO(contents))

    # Record in DB
    rec = crud.record_document_upload(
        db,
        session_id,
        doc_type or "unknown",
        file.filename,
        local_path,
        content_type,
    )

    return {
        "status": "ok",
        "id": rec.id,
        "filename": rec.filename,
        "uploaded_at": str(rec.uploaded_at),
    }


@app.get("/session_uploads/{session_id}")
async def session_uploads(session_id: str, db: Session = Depends(get_db)):
    """Fetch all uploads under a given session."""
    rows = crud.list_uploads_for_session(db, session_id)
    data = [
        {
            "id": r.id,
            "doc_type": r.doc_type,
            "filename": r.filename,
            "uploaded_at": str(r.uploaded_at),
        }
        for r in rows
    ]
    return JSONResponse(data)


@app.get("/uploads/{session_id}/{filename}")
async def serve_uploaded(session_id: str, filename: str):
    """Serve uploaded file for review."""
    path = os.path.join(UPLOAD_DIR, session_id, filename)
    if not os.path.exists(path):
        raise HTTPException(status_code=404, detail="File not found")

    return FileResponse(path)
