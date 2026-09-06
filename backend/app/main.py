import os
from pathlib import Path
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from .database import engine, Base, run_migrations
from .routers import candidate, assessment, proctoring, manager

# Create SQLite tables, then apply additive migrations for the adaptive-engine columns
# on any pre-existing database (keeps historical submissions intact).
Base.metadata.create_all(bind=engine)
run_migrations()

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
