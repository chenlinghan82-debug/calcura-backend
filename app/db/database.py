import os
from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker
BASE_DIR = Path(__file__).resolve().parents[2]


def normalize_database_url(url: str) -> str:
    """Use psycopg v3 for Postgres while leaving SQLite URLs unchanged."""
    cleaned = url.strip()
    if cleaned.startswith("postgres://"):
        return "postgresql+psycopg://" + cleaned[len("postgres://") :]
    if cleaned.startswith("postgresql://"):
        return "postgresql+psycopg://" + cleaned[len("postgresql://") :]
    return cleaned


def resolve_database_url() -> str:
    configured = (
        os.getenv("CALCULATOR_DATABASE_URL")
        or os.getenv("POSTGRES_URL")
        or os.getenv("DATABASE_URL")
        or os.getenv("POSTGRES_URL_NON_POOLING")
        or os.getenv("DATABASE_URL_UNPOOLED")
    )
    if configured:
        return normalize_database_url(configured)
    data_dir = Path("/tmp") if os.getenv("VERCEL") else BASE_DIR / "data"
    data_dir.mkdir(exist_ok=True)
    return f"sqlite:///{(data_dir / 'calculator.db').as_posix()}"


DATABASE_URL = resolve_database_url()
IS_SQLITE = DATABASE_URL.startswith("sqlite")

engine_options: dict = {}
if IS_SQLITE:
    engine_options["connect_args"] = {"check_same_thread": False}
else:
    # Reuse one connection inside a warm serverless instance. pool_pre_ping
    # drops a connection that Neon closed while the instance was frozen.
    # prepare_threshold=None is required by Neon's pooled PgBouncer endpoint.
    engine_options["pool_size"] = 1
    engine_options["max_overflow"] = 1
    engine_options["pool_timeout"] = 10
    engine_options["pool_recycle"] = 280
    engine_options["pool_pre_ping"] = True
    engine_options["connect_args"] = {"prepare_threshold": None}

engine = create_engine(DATABASE_URL, **engine_options)
SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)


class Base(DeclarativeBase):
    pass


_schema_ready = False


def ensure_schema() -> None:
    """Create tables on the first real database use, not during import."""
    global _schema_ready
    if _schema_ready:
        return
    from app.models.history import CalculationHistory  # noqa: F401

    Base.metadata.create_all(bind=engine)
    if IS_SQLITE:
        with engine.begin() as connection:
            rows = connection.exec_driver_sql("PRAGMA table_info(calculation_history)").fetchall()
            columns = {row[1] for row in rows}
            if "is_favorite" not in columns:
                connection.exec_driver_sql(
                    "ALTER TABLE calculation_history ADD COLUMN is_favorite BOOLEAN NOT NULL DEFAULT 0"
                )
            if "steps_json" not in columns:
                connection.exec_driver_sql(
                    "ALTER TABLE calculation_history ADD COLUMN steps_json VARCHAR(2000) NOT NULL DEFAULT '[]'"
                )
    _schema_ready = True


def get_db():
    ensure_schema()
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
