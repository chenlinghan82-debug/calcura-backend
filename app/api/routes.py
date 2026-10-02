from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import delete, func, select
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.models.history import CalculationHistory
from app.schemas.history import (
    CalculateRequest,
    CalculateResponse,
    CalculationRecord,
    ClearResponse,
    DeleteResponse,
    HistoryResponse,
    StatsResponse,
)
from app.services.calculator import CalculationError, calculate_expression

router = APIRouter(prefix="/api")


@router.get("/health")
def health() -> dict[str, str | bool]:
    return {"success": True, "status": "ok"}


@router.post(
    "/calculate",
    response_model=CalculateResponse,
    status_code=status.HTTP_201_CREATED,
)
def calculate(request: CalculateRequest, db: Session = Depends(get_db)) -> CalculateResponse:
    try:
        result = calculate_expression(request.expression)
    except CalculationError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"success": False, "message": str(exc)},
        ) from exc

    record = CalculationHistory(expression=request.expression, result=result)
    db.add(record)
    db.commit()
    db.refresh(record)
    return CalculateResponse(
        expression=record.expression,
        result=record.result,
        record=CalculationRecord.model_validate(record),
    )


@router.get("/history", response_model=HistoryResponse)
def list_history(
    keyword: str | None = Query(default=None, max_length=100),
    limit: int = Query(default=100, ge=1, le=200),
    db: Session = Depends(get_db),
) -> HistoryResponse:
    statement = select(CalculationHistory).order_by(CalculationHistory.created_at.desc())
    if keyword and keyword.strip():
        statement = statement.where(CalculationHistory.expression.contains(keyword.strip()))
    items = db.scalars(statement.limit(limit)).all()
    total_statement = select(func.count()).select_from(CalculationHistory)
    if keyword and keyword.strip():
        total_statement = total_statement.where(
            CalculationHistory.expression.contains(keyword.strip())
        )
    total = db.scalar(total_statement) or 0
    return HistoryResponse(
        items=[CalculationRecord.model_validate(item) for item in items],
        total=total,
    )


@router.delete("/history/{record_id}", response_model=DeleteResponse)
def delete_history(record_id: int, db: Session = Depends(get_db)) -> DeleteResponse:
    record = db.get(CalculationHistory, record_id)
    if record is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"success": False, "message": "History record not found"},
        )
    db.delete(record)
    db.commit()
    return DeleteResponse(message="History record deleted")


@router.delete("/history", response_model=ClearResponse)
def clear_history(db: Session = Depends(get_db)) -> ClearResponse:
    deleted_count = db.query(CalculationHistory).delete()
    db.commit()
    return ClearResponse(deleted_count=deleted_count)


@router.get("/stats", response_model=StatsResponse)
def get_stats(db: Session = Depends(get_db)) -> StatsResponse:
    total, average, minimum, maximum = db.execute(
        select(
            func.count(CalculationHistory.id),
            func.avg(CalculationHistory.result),
            func.min(CalculationHistory.result),
            func.max(CalculationHistory.result),
        )
    ).one()
    return StatsResponse(
        total=total or 0,
        average=float(average) if average is not None else None,
        minimum=float(minimum) if minimum is not None else None,
        maximum=float(maximum) if maximum is not None else None,
    )
