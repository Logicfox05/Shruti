import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent  # .../backend

# The question bank ships with the code and is read-only.
DATA_DIR = os.path.join(BASE_DIR, "app", "data")

# Writable locations — overridable via environment so a hosted deploy (e.g. Render) can
# point them at a persistent disk instead of the ephemeral container filesystem.
UPLOAD_DIR = os.environ.get("UPLOAD_DIR") or os.path.join(BASE_DIR, "uploads")
DATABASE_URL = os.environ.get("DATABASE_URL") or f"sqlite:///{os.path.join(BASE_DIR, 'smarthire.db')}"

os.makedirs(UPLOAD_DIR, exist_ok=True)

# Manager portal password. MUST be set via the MANAGER_PASSWORD environment variable in
# production; the default is for local development only.
MANAGER_PASSWORD = os.environ.get("MANAGER_PASSWORD", "admin123")

# Total Assessment Architecture: 80 Questions / 60 Mins
TOTAL_ASSESSMENT_QUESTIONS = 80
FINANCE_QUESTIONS_COUNT = 48          # 60% Core Accounts & Finance
IQ_ADAPTABILITY_QUESTIONS_COUNT = 16  # 20% IQ & Workplace Adaptability
RESUME_QUESTIONS_COUNT = 16           # 20% Dynamic Resume Verification
ASSESSMENT_DURATION_MINUTES = 60
