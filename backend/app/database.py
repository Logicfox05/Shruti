from sqlalchemy import create_engine, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from .config import DATABASE_URL

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False}
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# Columns introduced for the adaptive engine. Added to any pre-existing SQLite
# database via ADD COLUMN so historical rows survive with sensible backfill values.
# Old (already-submitted) sessions get current_section='complete' so the adaptive
# logic never re-touches them.
_ADAPTIVE_COLUMNS = [
    ("current_section", "TEXT DEFAULT 'complete'"),
    ("current_tier", "TEXT DEFAULT 'Basic'"),
    ("current_batch_size", "INTEGER DEFAULT 0"),
    ("finance_served", "INTEGER DEFAULT 0"),
    ("iq_served", "INTEGER DEFAULT 0"),
    ("resume_served", "INTEGER DEFAULT 0"),
    ("pending_resume", "TEXT"),
]

def run_migrations():
    """Idempotent, additive SQLite migration: add any missing columns without dropping
    data. Safe to run on every startup."""
    with engine.begin() as conn:
        sess_cols = {row[1] for row in conn.execute(text("PRAGMA table_info(assessment_sessions)"))}
        if sess_cols:
            for name, ddl in _ADAPTIVE_COLUMNS:
                if name not in sess_cols:
                    conn.execute(text(f"ALTER TABLE assessment_sessions ADD COLUMN {name} {ddl}"))

        proc_cols = {row[1] for row in conn.execute(text("PRAGMA table_info(proctoring_events)"))}
        if proc_cols and "client_time" not in proc_cols:
            conn.execute(text("ALTER TABLE proctoring_events ADD COLUMN client_time TEXT"))
