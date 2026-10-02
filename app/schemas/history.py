from datetime import datetime, timezone

from pydantic import BaseModel, Field, field_serializer, field_validator


class CalculateRequest(BaseModel):
    expression: str = Field(min_length=1, max_length=200)

    @field_validator("expression")
    @classmethod
    def expression_must_not_be_blank(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("Expression cannot be blank")
        return value


class CalculationRecord(BaseModel):
    id: int
    expression: str
    result: float
    created_at: datetime

    @field_serializer("created_at")
    def serialize_created_at(self, value: datetime) -> str:
        # SQLite returns naive datetimes even though the application stores UTC.
        # Treat a naive value as UTC and always expose an explicit ISO-8601 offset.
        normalized = value.replace(tzinfo=timezone.utc) if value.tzinfo is None else value.astimezone(timezone.utc)
        return normalized.isoformat(timespec="milliseconds").replace("+00:00", "Z")

    model_config = {"from_attributes": True}


class CalculateResponse(BaseModel):
    success: bool = True
    expression: str
    result: float
    record: CalculationRecord


class HistoryResponse(BaseModel):
    success: bool = True
    items: list[CalculationRecord]
    total: int


class DeleteResponse(BaseModel):
    success: bool = True
    message: str


class ClearResponse(BaseModel):
    success: bool = True
    deleted_count: int


class StatsResponse(BaseModel):
    success: bool = True
    total: int
    average: float | None = None
    minimum: float | None = None
    maximum: float | None = None
