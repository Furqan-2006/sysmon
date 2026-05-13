import os
from pathlib import Path

BASE_DIR = Path(__file__).parent

class Config:
    # ── Security ──────────────────────────────
    SECRET_KEY             = os.getenv("SECRET_KEY", "dev-secret-change-in-production")
    JWT_SECRET_KEY         = os.getenv("JWT_SECRET_KEY", "jwt-secret-change-in-production")
    JWT_ACCESS_TOKEN_EXPIRES = 3600  # 1 hour

    # ── Database ──────────────────────────────
    SQLALCHEMY_DATABASE_URI    = f"sqlite:///{BASE_DIR / 'instance' / 'sysmon.db'}"
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # ── File Upload ───────────────────────────
    UPLOAD_FOLDER    = str(BASE_DIR / "uploads")
    ALLOWED_EXTENSIONS = {"json", "yaml", "yml", "ini", "toml"}
    MAX_CONTENT_LENGTH = 2 * 1024 * 1024  # 2 MB max config file

    # ── C Extension ───────────────────────────
    C_LIB_PATH = str(BASE_DIR / "c_extension" / "sysmon.so")

    # ── History ───────────────────────────────
    METRICS_HISTORY_LIMIT = 100   # max rows returned in history queries
