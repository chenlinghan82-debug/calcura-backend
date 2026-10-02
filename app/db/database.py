import os
from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

BASE_DIR = Path(__file__).resolve().parents[2]
DATA_DIR = Path("/tmp") if os.getenv("VERCEL") else BASE_DIR / "data"
DATA_DIR.mkdir(exist_ok=True)
DATABASE_URL = os.getenv(
    "CALCULATOR_DATABASE_URL",
    f"sqlite:///{(DATA_DIR / 'calculator.db').as_posix()}",
)

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {},
)
SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)


class Base(DeclarativeBase):
    pass


def ensure_schema() -> None:
    """Create tables and add columns introduced after the first deployment."""
    from app.models.history import CalculationHistory  # noqa: F401

    Base.metadata.create_all(bind=engine)
    if not str(engine.url).startswith("sqlite"):
        return
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


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
