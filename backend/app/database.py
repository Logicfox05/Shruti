from sqlalchemy import create_engine, text, inspect
from sqlalchemy.orm import declarative_base, sessionmaker
from .config import DATABASE_URL, IS_POSTGRES, IS_SQLITE

# ---------------------------------------------------------------------------
# Engine
# ---------------------------------------------------------------------------
# SQLite (development) and PostgreSQL (production) need different engine options, so the
# same code runs against either. Managed Postgres providers drop idle connections, hence
# pool_pre_ping (verify before use) and pool_recycle (retire connections before the
# provider does).
if IS_SQLITE:
    engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
else:
    engine = create_engine(
        DATABASE_URL,
        pool_pre_ping=True,
        pool_recycle=300,
        pool_size=5,
        max_overflow=5,
        pool_timeout=30,
    )

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# ---------------------------------------------------------------------------
# Additive migrations
# ---------------------------------------------------------------------------
# Columns added after the first release. Types are given per dialect because SQLite and
# PostgreSQL spell them differently (notably BLOB vs BYTEA). Adding a column is safe and
# idempotent: existing rows keep their data and receive the default.
_MIGRATIONS = {
    "assessment_sessions": [
        ("current_section",    {"sqlite": "TEXT DEFAULT 'complete'", "postgresql": "TEXT DEFAULT 'complete'"}),
        ("current_tier",       {"sqlite": "TEXT DEFAULT 'Basic'",    "postgresql": "TEXT DEFAULT 'Basic'"}),
        ("current_batch_size", {"sqlite": "INTEGER DEFAULT 0",         "postgresql": "INTEGER DEFAULT 0"}),
        ("finance_served",     {"sqlite": "INTEGER DEFAULT 0",         "postgresql": "INTEGER DEFAULT 0"}),
        ("iq_served",          {"sqlite": "INTEGER DEFAULT 0",         "postgresql": "INTEGER DEFAULT 0"}),
        ("resume_served",      {"sqlite": "INTEGER DEFAULT 0",         "postgresql": "INTEGER DEFAULT 0"}),
        ("pending_resume",     {"sqlite": "TEXT",                      "postgresql": "TEXT"}),
    ],
    "proctoring_events": [
        ("client_time", {"sqlite": "TEXT", "postgresql": "TEXT"}),
    ],
    # Resume files are stored IN the database so they survive on hosts with an ephemeral
    # filesystem (the same reason the database itself moved off local disk).
    "candidates": [
        ("resume_data", {"sqlite": "BLOB",    "postgresql": "BYTEA"}),
        ("resume_mime", {"sqlite": "TEXT",    "postgresql": "TEXT"}),
        ("resume_size", {"sqlite": "INTEGER", "postgresql": "INTEGER"}),
    ],
}


def _existing_columns(conn, table: str):
    """Column names for `table`, or an empty set if the table does not exist yet."""
    inspector = inspect(conn)
    if table not in inspector.get_table_names():
        return set()
    return {col["name"] for col in inspector.get_columns(table)}


# Indexes that matter for the manager dashboard (listing, filtering, joins). `create_all`
# only builds indexes for tables it creates, so pre-existing databases get them here.
# `IF NOT EXISTS` is supported by both SQLite and PostgreSQL.
_INDEXES = [
    ("ix_candidates_email", "candidates", "email"),
    ("ix_candidates_created_at", "candidates", "created_at"),
    ("ix_assessment_sessions_candidate_id", "assessment_sessions", "candidate_id"),
    ("ix_assessment_sessions_created_at", "assessment_sessions", "created_at"),
    ("ix_sessions_status", "assessment_sessions", "status"),
    ("ix_session_questions_session_id", "session_questions", "session_id"),
    ("ix_proctoring_events_session_id", "proctoring_events", "session_id"),
]


def run_migrations():
    """Idempotent, additive migration that works on both SQLite and PostgreSQL.
    Adds any missing columns and indexes without touching existing data.
    Safe to run on every startup."""
    dialect = "postgresql" if IS_POSTGRES else "sqlite"
    with engine.begin() as conn:
        for table, columns in _MIGRATIONS.items():
            present = _existing_columns(conn, table)
            if not present:
                continue  # brand-new database: create_all() builds it fully
            for name, ddl_by_dialect in columns:
                if name not in present:
                    ddl = ddl_by_dialect[dialect]
                    conn.execute(text(f"ALTER TABLE {table} ADD COLUMN {name} {ddl}"))

        existing_tables = set(inspect(conn).get_table_names())
        for index_name, table, column in _INDEXES:
            if table in existing_tables:
                conn.execute(text(
                    f"CREATE INDEX IF NOT EXISTS {index_name} ON {table} ({column})"
                ))
