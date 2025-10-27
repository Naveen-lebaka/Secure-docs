import os
import qrcode
import base64
import io
import json
from cryptography.fernet import Fernet
from .config import settings

FILES_DIR = os.path.join(os.getcwd(), "files")
if not os.path.exists(FILES_DIR):
    os.makedirs(FILES_DIR, exist_ok=True)


def get_fernet():
    key = settings.fernet_key
    if not key:
        key = Fernet.generate_key().decode()
        settings.fernet_key = key
    return Fernet(key.encode())


def encrypt_and_save_file(file_data: bytes, filename: str):
    f = get_fernet()
    token = f.encrypt(file_data)
    safe_name = filename
    path = os.path.join(FILES_DIR, safe_name + ".enc")
    with open(path, "wb") as fh:
        fh.write(token)
    return path


def decrypt_file_to_bytes(path: str):
    f = get_fernet()
    with open(path, "rb") as fh:
        token = fh.read()
    return f.decrypt(token)


def generate_qr_base64(text: str):
    img = qrcode.make(text)
    buffered = io.BytesIO()
    img.save(buffered, format="PNG")
    img_b64 = base64.b64encode(buffered.getvalue()).decode()
    return "data:image/png;base64," + img_b64
