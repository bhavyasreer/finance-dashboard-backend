from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field, RootModel


class DashboardSummaryOut(BaseModel):
    total_income: float
    total_expense: float
    net_balance: float
    top_spending_category: str | None
    average_expense: float
    transaction_count: int

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "total_income": 100000.0,
                "total_expense": 50000.0,
                "net_balance": 50000.0,
                "top_spending_category": "Food",
                "average_expense": 10000.0,
                "transaction_count": 5,
            }
        }
    )


class CategoryBreakdownItem(BaseModel):
    """Single category aggregate from ``GET /dashboard/category-breakdown``."""

    category: str
    total: float

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "category": "Food",
                "total": 20000.0,
            }
        }
    )


class CategoryBreakdownOut(RootModel[list[CategoryBreakdownItem]]):
    """Response body: JSON array of category totals."""

    model_config = ConfigDict(
        json_schema_extra={
            "example": [
                {"category": "Food", "total": 20000.0},
                {"category": "Transport", "total": 10000.0},
            ]
        }
    )


class DashboardTrendRow(BaseModel):
    """
    One bucket from ``GET /dashboard/monthly-trends``.

    Daily mode: ``date`` is set (``YYYY-MM-DD``), ``month`` is omitted.
    Monthly mode: ``month`` is set (``YYYY-MM``), ``date`` is omitted.
    """

    date: str | None = None
    month: str | None = None
    income: float
    expense: float

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "date": "2026-04-01",
                "income": 500.0,
                "expense": 200.0,
            }
        }
    )


class DashboardTrendsOut(RootModel[list[DashboardTrendRow]]):
    """Response body: JSON array of daily or monthly buckets."""

    model_config = ConfigDict(
        json_schema_extra={
            "example": [
                {"date": "2026-04-01", "income": 500.0, "expense": 200.0},
                {"date": "2026-04-02", "income": 700.0, "expense": 350.0},
            ]
        }
    )


class RecentActivityItem(BaseModel):
    id: int
    amount: float
    type: str
    category: str
    sub_category: str | None = None
    date: str | None = None
    notes: str | None = None
    currency: str = Field(default="INR")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "id": 1,
                "amount": 500.0,
                "type": "expense",
                "category": "food",
                "sub_category": None,
                "date": "2026-04-02",
                "notes": "Lunch",
                "currency": "INR",
            }
        }
    )


class RecentActivityOut(RootModel[list[RecentActivityItem]]):
    """Response body: JSON array of recent transactions (projected fields)."""

    model_config = ConfigDict(
        json_schema_extra={
            "example": [
                {
                    "id": 1,
                    "amount": 500.0,
                    "type": "expense",
                    "category": "food",
                    "sub_category": None,
                    "date": "2026-04-02",
                    "notes": "Lunch",
                    "currency": "INR",
                }
            ]
        }
    )
