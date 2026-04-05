from __future__ import annotations

from typing import Any

from fastapi import status
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.core.auth import raise_api_error
from app.models.record import Record


def _ensure_record_active(record: Record) -> None:
    if record.is_deleted:
        raise_api_error(
            status.HTTP_404_NOT_FOUND,
            "RECORD_NOT_FOUND",
            f"Record with id {record.id} not found",
        )


def create_record(db: Session, data, user_id: int) -> Record:
    record = Record(**data.model_dump(), user_id=user_id)
    db.add(record)
    db.commit()
    db.refresh(record)
    return record


def get_records(
    db: Session,
    _current_user: Any,
    filters: dict[str, Any],
    *,
    page: int,
    limit: int,
) -> tuple[list[Record], int]:
    """
    List non-deleted records with optional filters and pagination.

    Search applies only to ``notes`` (case-insensitive substring). Use ``category`` /
    ``type`` query params for structured filters.
    """
    query = db.query(Record).filter(Record.is_deleted.is_(False))

    start_date = filters.get("start_date")
    end_date = filters.get("end_date")
    if start_date and end_date and start_date > end_date:
        raise_api_error(status.HTTP_400_BAD_REQUEST, "INVALID_DATE_RANGE", "start_date must be <= end_date")

    if filters.get("type"):
        query = query.filter(func.lower(Record.type) == filters["type"].strip().lower())
    if filters.get("category"):
        query = query.filter(func.lower(Record.category) == filters["category"].strip().lower())

    if start_date:
        query = query.filter(Record.date >= start_date)
    if end_date:
        query = query.filter(Record.date <= end_date)

    term = (filters.get("search") or "").strip()
    if term:
        pattern = f"%{term.lower()}%"
        query = query.filter(
            func.lower(func.coalesce(Record.notes, "")).like(pattern),
        )

    total = query.count()

    items = (
        query.order_by(Record.date.desc(), Record.id.desc())
        .offset((page - 1) * limit)
        .limit(limit)
        .all()
    )
    return items, total

def get_record_by_id(db: Session, record_id: int) -> Record:
    record = (
        db.query(Record)
        .filter(Record.id == record_id, Record.is_deleted.is_(False))
        .first()
    )

    if not record:
        raise_api_error(
            status.HTTP_404_NOT_FOUND,
            "RECORD_NOT_FOUND",
            f"Record with id {record_id} not found",
        )

    return record


def update_record(db: Session, record: Record, data) -> Record:
    _ensure_record_active(record)

    # Only apply fields present in the request (exclude_unset), and ignore None.
    update_data = data.model_dump(exclude_unset=True, exclude_none=True)
    for key, value in update_data.items():
        setattr(record, key, value)

    db.commit()
    db.refresh(record)
    return record


def soft_delete_record(db: Session, record: Record) -> dict[str, Any]:
    _ensure_record_active(record)

    record.is_deleted = True
    db.commit()
    db.refresh(record)
    return {"id": record.id, "deleted": True}