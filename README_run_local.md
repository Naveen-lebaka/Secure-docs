# Run locally (Windows / Linux / Mac)

1. Create project dir and files as provided. Ensure structure matches.

2. Create virtual environment:
   python -m venv venv
   # Activate:
   # Windows: venv\Scripts\activate
   # Mac/Linux: source venv/bin/activate

3. Install:
   pip install -r requirements.txt

4. Create an .env file in the project root (same level as requirements.txt) based on .env.example
   Example .env:
     SECRET_KEY=mysupersecretkey123
     FERNET_KEY=         # you can leave empty; first run will generate it
     ACCESS_TOKEN_EXPIRE_MINUTES=60
     BASE_URL=http://192.168.1.50:8000   # change to your laptop IP to test from phone

5. Start the server:
   uvicorn app.main:app --host 192.168.0.103 --port 8000 --reload

6. Access from browser on laptop:
   http://127.0.0.1:8000/

7. To test from phone, find your laptop local IP (e.g., 192.168.1.50) and set BASE_URL in .env to that value, then open:
   http://192.168.1.50:8000/verify/<token> (or http://192.168.1.50:8000/)

8. Example quick flow:
   - Register user: POST /api/auth/register   (JSON: {"email":"me@x.com","password":"pass","full_name":"Me"})
   - Login: POST /api/auth/login (OAuth2 form data username=<email> password=<password>) -> get token
   - Upload file via /static/upload.html (enter token)
   - Create verification request: POST /api/verification-requests (form) e.g. verifier_name=CompanyX requested_fields=["passport"]
     You'll get a token and a QR image in response (base64) and a link.
   - Open the link on phone; login; Share the doc; verifier will get download link.

9. Files are stored encrypted in ./files folder.

10. When done, stop server (Ctrl+C). The sqlite DB is app.db in project root.

