import csv
import io
import json

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import Response
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.models.history import CalculationHistory
from app.schemas.history import (
    CalculateRequest,
    CalculateResponse,
    CalculationRecord,
    ClearResponse,
    DeleteResponse,
    FavoriteResponse,
    HistoryResponse,
    StatsResponse,
)
from app.services.calculator import CalculationError, explain_expression

router = APIRouter(prefix="/api")


def dump_steps(steps: list[str]) -> str:
    payload = list(steps)
    while payload and len(json.dumps(payload)) > 1800:
        payload.pop()
    return json.dumps(payload)


def load_steps(value: str | None) -> list[str]:
    try:
        parsed = json.loads(value or "[]")
    except json.JSONDecodeError:
        return []
    if not isinstance(parsed, list):
        return []
    return [str(item) for item in parsed]


def to_record(item: CalculationHistory) -> CalculationRecord:
    return CalculationRecord(
        id=item.id,
        expression=item.expression,
        result=item.result,
        is_favorite=bool(item.is_favorite),
        steps=load_steps(item.steps_json),
        created_at=item.created_at,
    )


def history_query(keyword: str | None):
    statement = select(CalculationHistory).order_by(CalculationHistory.created_at.desc())
    if keyword and keyword.strip():
        statement = statement.where(CalculationHistory.expression.contains(keyword.strip()))
    return statement


@router.get("/health")
def health() -> dict[str, str | bool]:
    return {"success": True, "status": "ok"}


@router.post(
    "/calculate",
    response_model=CalculateResponse,
    status_code=status.HTTP_201_CREATED,
)
def calculate(request: CalculateRequest, db: Session = Depends(get_db)) -> CalculateResponse:
    latest = db.scalar(select(CalculationHistory).order_by(CalculationHistory.id.desc()))
    ans = None if latest is None else latest.result
    try:
        result, steps = explain_expression(request.expression, ans)
    except CalculationError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"success": False, "message": str(exc)},
        ) from exc

    record = CalculationHistory(
        expression=request.expression,
        result=result,
        is_favorite=False,
        steps_json=dump_steps(steps),
    )
    db.add(record)
    db.commit()
    db.refresh(record)
    stored = to_record(record)
    return CalculateResponse(
        expression=record.expression,
        result=record.result,
        steps=stored.steps,
        record=stored,
    )


@router.get("/history", response_model=HistoryResponse)
def list_history(
    keyword: str | None = Query(default=None, max_length=100),
    limit: int = Query(default=100, ge=1, le=200),
    db: Session = Depends(get_db),
) -> HistoryResponse:
    items = db.scalars(history_query(keyword).limit(limit)).all()
    total_statement = select(func.count()).select_from(CalculationHistory)
    if keyword and keyword.strip():
        total_statement = total_statement.where(CalculationHistory.expression.contains(keyword.strip()))
    total = db.scalar(total_statement) or 0
    return HistoryResponse(items=[to_record(item) for item in items], total=total)


@router.get("/history/export")
def export_history(
    keyword: str | None = Query(default=None, max_length=100),
    db: Session = Depends(get_db),
) -> Response:
    items = db.scalars(history_query(keyword).limit(1000)).all()
    buffer = io.StringIO()
    writer = csv.writer(buffer)
    writer.writerow(["id", "expression", "result", "created_at", "is_favorite", "steps"])
    for item in items:
        record = to_record(item)
        writer.writerow([
            record.id,
            record.expression,
            record.result,
            record.created_at.isoformat(),
            record.is_favorite,
            " | ".join(record.steps),
        ])
    return Response(
        content=buffer.getvalue(),
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": "attachment; filename=calcura-history.csv"},
    )


@router.post("/history/{record_id}/favorite", response_model=FavoriteResponse)
def toggle_favorite(record_id: int, db: Session = Depends(get_db)) -> FavoriteResponse:
    record = db.get(CalculationHistory, record_id)
    if record is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"success": False, "message": "History record not found"},
        )
    record.is_favorite = not bool(record.is_favorite)
    db.commit()
    db.refresh(record)
    return FavoriteResponse(record=to_record(record))


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
