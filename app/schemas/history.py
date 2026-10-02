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
    is_favorite: bool = False
    steps: list[str] = Field(default_factory=list)
    created_at: datetime

    @field_serializer("created_at")
    def serialize_created_at(self, value: datetime) -> str:
        normalized = value.replace(tzinfo=timezone.utc) if value.tzinfo is None else value.astimezone(timezone.utc)
        return normalized.isoformat(timespec="milliseconds").replace("+00:00", "Z")

    model_config = {"from_attributes": True}


class CalculateResponse(BaseModel):
    success: bool = True
    expression: str
    result: float
    steps: list[str]
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


class FavoriteResponse(BaseModel):
    success: bool = True
    record: CalculationRecord


class StatsResponse(BaseModel):
    success: bool = True
    total: int
    average: float | None = None
    minimum: float | None = None
    maximum: float | None = None


class PreviewResponse(BaseModel):
    success: bool = True
    expression: str
    result: float
    steps: list[str]
    saved: bool = False
