import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
IS_VERCEL = os.getenv("VERCEL") == "1"
DEFAULT_DATABASE = (
    Path("/tmp/print_navbati.sqlite3")
    if IS_VERCEL
    else BASE_DIR / "instance" / "print_navbati.sqlite3"
)
DEFAULT_UPLOAD_FOLDER = (
    Path("/tmp/print_navbati_uploads")
    if IS_VERCEL
    else BASE_DIR / "uploads"
)


class Config:
    SECRET_KEY = os.getenv("SECRET_KEY")
    if not SECRET_KEY and IS_VERCEL:
        raise RuntimeError("Set the SECRET_KEY environment variable in Vercel.")
    SECRET_KEY = SECRET_KEY or "dev-key-change-me"
    SQLALCHEMY_DATABASE_URI = os.getenv(
        "DATABASE_URL", f"sqlite:///{DEFAULT_DATABASE}"
    )
    IS_VERCEL = IS_VERCEL
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"
    SESSION_COOKIE_SECURE = IS_VERCEL
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024
    UPLOAD_FOLDER = os.getenv("UPLOAD_FOLDER", str(DEFAULT_UPLOAD_FOLDER))
    ALLOWED_EXTENSIONS = {"pdf"}
