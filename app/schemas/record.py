from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from typing import List, Literal, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator

RecordType = Literal["income", "expense"]
RecordSource = Literal["manual", "import", "system"]


def _currency_validator(v: str) -> str:
    if not isinstance(v, str) or len(v) != 3 or not v.isalpha() or v != v.upper():
        raise ValueError("Currency must be a 3-letter uppercase code")
    return v


_RECORD_OUT_EXAMPLE: dict = {
    "id": 1,
    "user_id": 2,
    "amount": 500,
    "type": "expense",
    "category": "food",
    "sub_category": None,
    "date": "2026-04-02",
    "notes": "Lunch",
    "source": "manual",
    "reference_id": None,
    "currency": "INR",
    "is_deleted": False,
    "created_at": "2026-04-02T12:30:00+00:00",
    "updated_at": "2026-04-02T12:30:00+00:00",
}


class RecordCreate(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "amount": 500,
                "type": "expense",
                "category": "food",
                "sub_category": None,
                "date": "2026-04-02",
                "notes": "Lunch",
                "source": "manual",
                "reference_id": None,
                "currency": "INR",
            }
        }
    )

    amount: Decimal
    type: RecordType
    category: str = Field(min_length=1, max_length=100)
    sub_category: Optional[str] = Field(default=None, max_length=100)
    date: date
    notes: Optional[str] = None

    source: RecordSource = "manual"
    reference_id: Optional[str] = Field(default=None, max_length=100)
    currency: str = "INR"

    @field_validator("amount")
    @classmethod
    def amount_positive(cls, value: Decimal) -> Decimal:
        if value <= 0:
            raise ValueError("Amount must be greater than zero")
        return value

    @field_validator("date")
    @classmethod
    def date_not_future(cls, value: date) -> date:
        if value > date.today():
            raise ValueError("Date must not be in the future")
        return value

    @field_validator("currency")
    @classmethod
    def currency_code(cls, value: str) -> str:
        return _currency_validator(value)


class RecordUpdate(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "amount": 750,
                "notes": "Team lunch (updated)",
            }
        }
    )

    amount: Optional[Decimal] = None
    type: Optional[RecordType] = None
    category: Optional[str] = Field(default=None, min_length=1, max_length=100)
    sub_category: Optional[str] = Field(default=None, max_length=100)
    date: Optional[date] = None
    notes: Optional[str] = None

    source: Optional[RecordSource] = None
    reference_id: Optional[str] = Field(default=None, max_length=100)
    currency: Optional[str] = None

    @field_validator("amount")
    @classmethod
    def amount_positive_when_set(cls, value: Optional[Decimal]) -> Optional[Decimal]:
        if value is not None and value <= 0:
            raise ValueError("Amount must be greater than zero")
        return value

    @field_validator("date")
    @classmethod
    def date_not_future_when_set(cls, value: Optional[date]) -> Optional[date]:
        if value is not None and value > date.today():
            raise ValueError("Date must not be in the future")
        return value

    @field_validator("currency")
    @classmethod
    def currency_code_when_set(cls, value: Optional[str]) -> Optional[str]:
        if value is None:
            return value
        return _currency_validator(value)


class PaginationMeta(BaseModel):
    page: int
    limit: int
    total: int

    model_config = ConfigDict(
        json_schema_extra={"example": {"page": 1, "limit": 10, "total": 25}}
    )


class RecordOut(BaseModel):
    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={"example": _RECORD_OUT_EXAMPLE},
    )

    id: int
    user_id: int
    amount: Decimal
    type: RecordType
    category: str
    sub_category: Optional[str] = None
    date: date
    notes: Optional[str] = None

    source: RecordSource = "manual"
    reference_id: Optional[str] = None
    currency: str = "INR"

    is_deleted: bool
    created_at: datetime
    updated_at: datetime | None = None


class RecordCreatedOut(RecordOut):
    message: str = Field(default="Record created successfully")

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                **_RECORD_OUT_EXAMPLE,
                "message": "Record created successfully",
            }
        },
    )


class RecordUpdatedOut(RecordOut):
    message: str = Field(default="Record updated successfully")

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                **_RECORD_OUT_EXAMPLE,
                "message": "Record updated successfully",
            }
        },
    )


class RecordDeletedOut(BaseModel):
    id: int
    deleted: bool
    message: str = Field(default="Record deleted successfully")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "id": 1,
                "deleted": True,
                "message": "Record deleted successfully",
            }
        }
    )


class RecordListResponse(BaseModel):
    """List payload with pagination; `message` is set when there are no matching records."""

    data: List[RecordOut]
    pagination: PaginationMeta
    message: Optional[str] = Field(
        default=None,
        description="Present when the filtered result set is empty.",
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "data": [_RECORD_OUT_EXAMPLE],
                "pagination": {"page": 1, "limit": 10, "total": 25},
                "message": None,
            }
        }
    )
