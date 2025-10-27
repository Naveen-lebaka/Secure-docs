from fastapi import FastAPI

# Create FastAPI instance
app = FastAPI(title="Secure Docs API", version="1.0.0")

# Root endpoint


@app.get("/")
def read_root():
    return {"message": "Welcome to Secure Docs API 🚀"}

# Another sample endpoint


@app.get("/health")
def health_check():
    return {"status": "OK", "message": "Server is running fine ✅"}
