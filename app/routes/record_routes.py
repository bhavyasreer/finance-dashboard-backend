from datetime import date

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.auth import require_permission, require_record_ownership_or_admin
from app.db.database import get_db
from app.schemas.record import (
    PaginationMeta,
    RecordCreate,
    RecordCreatedOut,
    RecordDeletedOut,
    RecordListResponse,
    RecordOut,
    RecordUpdate,
    RecordUpdatedOut,
)
from app.services.record_service import (
    create_record,
    get_record_by_id,
    get_records,
    soft_delete_record,
    update_record,
)

router = APIRouter()


@router.post("/", summary="Create Record", description="Create a new financial record (income or expense).")
def create(
    record: RecordCreate,
    db=Depends(get_db),
    current_user=Depends(require_permission("CREATE_RECORDS")),
) -> RecordCreatedOut:
    rec = create_record(db, record, current_user.id)
    return RecordCreatedOut.model_validate(rec)


@router.get(
    "/",
    summary="List Records",
    description=(
        "Paginated list with filters (type, category, date range). "
        "Optional ``search`` matches ``notes`` only (case-insensitive, partial)."
    ),
    response_model=RecordListResponse,
)
def list_records(
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1, le=50),
    type: str | None = Query(None),
    category: str | None = Query(None),
    search: str | None = Query(
        None,
        description="Case-insensitive partial match on notes only (combined with filters using AND).",
    ),
    start_date: date | None = Query(None),
    end_date: date | None = Query(None),
    db=Depends(get_db),
    current_user=Depends(require_permission("VIEW_RECORDS")),
):
    filters = {"type": type, "category": category, "start_date": start_date, "end_date": end_date}
    if search:
        filters["search"] = search

    items, total = get_records(db, current_user, filters, page=page, limit=limit)
    return RecordListResponse(
        data=items,
        pagination=PaginationMeta(page=page, limit=limit, total=total),
        message="No records found" if total == 0 else None,
    )


@router.get(
    "/{id}",
    summary="Get Record",
    description="Retrieve a specific record by id.",
    response_model=RecordOut,
)
def get_record(
    id: int,
    db: Session = Depends(get_db),
    _: object = Depends(require_permission("VIEW_RECORDS")),
):
    return get_record_by_id(db, id)


@router.patch("/{id}", summary="Update Record", description="Update an existing financial record.")
def update(
    id: int,
    data: RecordUpdate,
    db=Depends(get_db),
    _: object = Depends(require_permission("UPDATE_RECORDS")),
    record=Depends(require_record_ownership_or_admin),
) -> RecordUpdatedOut:
    rec = update_record(db, record, data)
    return RecordUpdatedOut.model_validate(rec)


@router.delete("/{id}", summary="Delete Record", description="Soft delete a record (marks as deleted).")
def delete(
    id: int,
    db=Depends(get_db),
    _: object = Depends(require_permission("DELETE_RECORDS")),
    record=Depends(require_record_ownership_or_admin),
) -> RecordDeletedOut:
    payload = soft_delete_record(db, record)
    return RecordDeletedOut(**payload)
