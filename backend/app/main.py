import os
from pathlib import Path
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from .config import DATABASE_URL, IS_POSTGRES, SECRET_KEY_IS_EPHEMERAL, MANAGER_PASSWORD
from .database import engine, Base, SessionLocal, run_migrations
from .auth import bootstrap_admin
from .routers import candidate, assessment, proctoring, manager

# Create any missing tables, then apply additive migrations (new columns and indexes) to
# an existing database so historical submissions are kept intact. Works on both SQLite
# (development) and PostgreSQL (production).
Base.metadata.create_all(bind=engine)
run_migrations()

# Seed the first administrator so a brand-new deployment can be signed into.
_bootstrap_db = SessionLocal()
try:
    _created = bootstrap_admin(_bootstrap_db)
    if _created:
        print(f"  {_created}")
finally:
    _bootstrap_db.close()

print(f"  Database: {'PostgreSQL' if IS_POSTGRES else 'SQLite'} ({DATABASE_URL.split('@')[-1].split('?')[0]})")
if not IS_POSTGRES:
    print("  WARNING: using SQLite. On a host with an ephemeral filesystem (e.g. Render's "
          "free plan) all candidate data is lost on restart. Set DATABASE_URL to a "
          "PostgreSQL URL in production.")
if SECRET_KEY_IS_EPHEMERAL:
    print("  WARNING: SECRET_KEY is not set, so a random one was generated. Manager "
          "sessions will be invalidated on every restart. Set SECRET_KEY in production.")
if MANAGER_PASSWORD == "admin123":
    print("  WARNING: MANAGER_PASSWORD is the default. Set a strong one before deploying.")

app = FastAPI(
    title="SmartHire Finance & Packaging Assessment System",
    version="1.0.0",
    description="Recruitment Intelligence Engine with SAP B1 & Indian Compliance Assessment"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API Routers
app.include_router(candidate.router)
app.include_router(assessment.router)
app.include_router(proctoring.router)
app.include_router(manager.router)

# Mount Frontend static files
FRONTEND_DIR = Path(__file__).resolve().parent.parent.parent / "frontend"

if FRONTEND_DIR.exists():
    app.mount("/css", StaticFiles(directory=str(FRONTEND_DIR / "css")), name="css")
    app.mount("/js", StaticFiles(directory=str(FRONTEND_DIR / "js")), name="js")

    @app.get("/")
    async def serve_frontend():
        return FileResponse(str(FRONTEND_DIR / "index.html"))

print("FastAPI Application initialized successfully.")
