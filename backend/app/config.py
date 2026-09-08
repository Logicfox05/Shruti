import os
import secrets
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent  # .../backend

# The question bank ships with the code and is read-only.
DATA_DIR = os.path.join(BASE_DIR, "app", "data")

# Writable location for resume files. NOTE: on an ephemeral host (e.g. Render's free
# plan) this directory is wiped on every restart, which is why uploaded resumes are ALSO
# stored as bytes in the database. This directory is only a local cache / legacy path.
UPLOAD_DIR = os.environ.get("UPLOAD_DIR") or os.path.join(BASE_DIR, "uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)


def _normalise_db_url(url: str) -> str:
    """Make a hosted Postgres URL usable by SQLAlchemy 2.x + psycopg 3.

    Render/Heroku hand out URLs beginning with `postgres://`, which SQLAlchemy 2 no
    longer recognises, and a bare `postgresql://` would try to load psycopg2 (not
    installed). Both are rewritten to the psycopg-3 driver. Also ensures SSL is
    requested for remote Postgres, which managed providers require.
    """
    if not url:
        return url
    if url.startswith("postgres://"):
        url = "postgresql+psycopg://" + url[len("postgres://"):]
    elif url.startswith("postgresql://"):
        url = "postgresql+psycopg://" + url[len("postgresql://"):]

    if url.startswith("postgresql+psycopg://") and "sslmode=" not in url:
        # Local Postgres usually has no TLS; managed providers require it.
        host_part = url.split("@")[-1].split("/")[0]
        if not host_part.startswith(("localhost", "127.0.0.1")):
            url += ("&" if "?" in url else "?") + "sslmode=require"
    return url


# Database. Defaults to a local SQLite file for development; set DATABASE_URL to a
# PostgreSQL URL in production (Render injects this automatically from the blueprint).
DATABASE_URL = _normalise_db_url(
    os.environ.get("DATABASE_URL") or f"sqlite:///{os.path.join(BASE_DIR, 'smarthire.db')}"
)
IS_POSTGRES = DATABASE_URL.startswith("postgresql")
IS_SQLITE = DATABASE_URL.startswith("sqlite")

# ---------------------------------------------------------------------------
# Manager portal credentials
# ---------------------------------------------------------------------------
# Manager accounts live in the `managers` table with bcrypt-hashed passwords. On first
# start, if that table is empty, a bootstrap admin is created from these variables so a
# fresh deploy is immediately usable. Change the password after first login.
MANAGER_EMAIL = os.environ.get("MANAGER_EMAIL", "admin@smarthire.local").strip().lower()
MANAGER_PASSWORD = os.environ.get("MANAGER_PASSWORD", "admin123")

# Secret used to sign manager session tokens. MUST be set in production: if it is left
# unset the value changes on every restart, which simply logs managers out.
SECRET_KEY = os.environ.get("SECRET_KEY") or secrets.token_hex(32)
SECRET_KEY_IS_EPHEMERAL = not os.environ.get("SECRET_KEY")

# How long a manager session token stays valid.
TOKEN_TTL_SECONDS = int(os.environ.get("TOKEN_TTL_SECONDS", 12 * 3600))

# Largest resume accepted (bytes). Stored in the database, so keep it modest.
MAX_RESUME_BYTES = int(os.environ.get("MAX_RESUME_BYTES", 10 * 1024 * 1024))

# Total Assessment Architecture: 80 Questions / 60 Mins
TOTAL_ASSESSMENT_QUESTIONS = 80
FINANCE_QUESTIONS_COUNT = 48          # 60% Core Accounts & Finance
IQ_ADAPTABILITY_QUESTIONS_COUNT = 16  # 20% IQ & Workplace Adaptability
RESUME_QUESTIONS_COUNT = 16           # 20% Dynamic Resume Verification
ASSESSMENT_DURATION_MINUTES = 60
