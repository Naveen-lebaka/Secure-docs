# app/utils.py
import qrcode
import io
import base64
from PIL import Image
import os
from dotenv import load_dotenv

load_dotenv()
UPLOAD_DIR = os.getenv("UPLOAD_DIR", "./uploads")


def generate_qr_dataurl(link: str) -> str:
    qr = qrcode.QRCode(box_size=6, border=2)
    qr.add_data(link)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white").convert("RGB")
    buffered = io.BytesIO()
    img.save(buffered, format="PNG")
    img_bytes = buffered.getvalue()
    b64 = base64.b64encode(img_bytes).decode()
    return f"data:image/png;base64,{b64}"


def save_upload_file(session_id: str, filename: str, fileobj, uploads_root: str = UPLOAD_DIR) -> str:
    folder = os.path.join(uploads_root, session_id)
    os.makedirs(folder, exist_ok=True)
    safe_name = filename.replace("/", "_").replace("..", "")
    path = os.path.join(folder, safe_name)
    with open(path, "wb") as f:
        f.write(fileobj.read())
    return path
