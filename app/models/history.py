from datetime import datetime, timezone

from sqlalchemy import DateTime, Float, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.database import Base


class CalculationHistory(Base):
    __tablename__ = "calculation_history"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    expression: Mapped[str] = mapped_column(String(200), nullable=False)
    result: Mapped[float] = mapped_column(Float, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
