from __future__ import annotations

from datetime import date, timedelta
from typing import Any

from fastapi import status
from sqlalchemy import case, func
from sqlalchemy.orm import Session

from app.core.auth import raise_api_error
from app.models.record import Record


def _base_query(db: Session, current_user: Any):
    # This dashboard represents organization-level financial insights.
    # Therefore, queries aggregate all records instead of filtering by individual users.
    #
    # Future extension: this can be adapted to support user-specific dashboards if required.
    return db.query(Record).filter(Record.is_deleted.is_(False))


def get_summary(db: Session, current_user: Any) -> dict[str, Any]:
    """
    All summary fields are computed using SQL aggregation (no raw record iteration).
    """
    q = _base_query(db, current_user)

    # Compute multiple aggregates in a single query.
    # - Income/expense use SUM(CASE ...)
    # - Avg expense uses AVG(CASE ...) where non-expenses become NULL (AVG ignores NULLs)
    totals_row = (
        q.with_entities(
            func.coalesce(
                func.sum(case((Record.type == "income", Record.amount), else_=0)),
                0,
            ).label("total_income"),
            func.coalesce(
                func.sum(case((Record.type == "expense", Record.amount), else_=0)),
                0,
            ).label("total_expense"),
            func.coalesce(
                func.avg(case((Record.type == "expense", Record.amount), else_=None)),
                0,
            ).label("avg_expense"),
            func.count(Record.id).label("transaction_count"),
        )
        .first()
    )

    if not totals_row:
        total_income = 0
        total_expense = 0
        avg_expense = 0
        transaction_count = 0
    else:
        total_income = totals_row.total_income
        total_expense = totals_row.total_expense
        avg_expense = totals_row.avg_expense
        transaction_count = totals_row.transaction_count

    top_spending_category_row = (
        q.with_entities(
            Record.category,
            func.coalesce(func.sum(Record.amount), 0).label("expense_sum"),
        )
        .filter(Record.type == "expense")
        .group_by(Record.category)
        .order_by(func.sum(Record.amount).desc())
        .limit(1)
        .first()
    )

    top_spending_category = (
        top_spending_category_row[0] if top_spending_category_row else None
    )

    # Keep JSON-friendly numbers.
    total_income = float(total_income)
    total_expense = float(total_expense)
    avg_expense = float(avg_expense)

    return {
        "total_income": total_income,
        "total_expense": total_expense,
        "net_balance": total_income - total_expense,
        "top_spending_category": top_spending_category,
        "average_expense": avg_expense,
        "transaction_count": int(transaction_count),
    }


def category_breakdown(db: Session, current_user: Any) -> dict[str, Any]:
    """
    Category totals computed with SQL GROUP BY.
    """
    q = _base_query(db, current_user)

    rows = (
        q.with_entities(
            Record.category,
            func.coalesce(func.sum(Record.amount), 0).label("category_total"),
        )
        .group_by(Record.category)
        .all()
    )

    # Aggregated rows are small; loop is over categories, not transactions.
    return [
    {
        "category": category,
        "total": float(total)
    }
    for category, total in rows
            ]


def _resolve_trend_date_range(
    start_date: date | None,
    end_date: date | None,
) -> tuple[date, date]:
    """
    If both are omitted: last 30 days through today (daily granularity by default rule).
    If only end_date: last 30 days ending on end_date.
    If only start_date: start_date through today.
    """
    today = date.today()
    if start_date is None and end_date is None:
        return today - timedelta(days=30), today
    if start_date is None and end_date is not None:
        return end_date - timedelta(days=30), end_date
    if start_date is not None and end_date is None:
        return start_date, today
    return start_date, end_date


def _format_bucket_date(value: Any) -> str:
    if hasattr(value, "isoformat"):
        return value.isoformat()
    s = str(value).strip()
    return s[:10] if len(s) >= 10 else s


def get_monthly_trends(
    db: Session,
    current_user: Any,
    *,
    start_date: date | None = None,
    end_date: date | None = None,
) -> list[dict[str, Any]]:
    """
    Income and expense trends for a date range, aggregated in SQL.

    * Range (end - start).days <= 31: one row per calendar day (`date`, `income`, `expense`).
    * Otherwise: one row per calendar month (`month`, `income`, `expense`).

    If `start_date` and `end_date` are both omitted, uses the last 30 days through today
    (daily buckets, since the span is <= 31 days).

    Empty result: [] (no placeholder rows).
    """
    start, end = _resolve_trend_date_range(start_date, end_date)
    if start > end:
        raise_api_error(
            status.HTTP_400_BAD_REQUEST,
            "INVALID_DATE_RANGE",
            "start_date must be less than or equal to end_date",
        )

    delta_days = (end - start).days
    use_daily = delta_days <= 31

    q = _base_query(db, current_user).filter(Record.date >= start, Record.date <= end)

    income_expr = func.coalesce(
        func.sum(case((Record.type == "income", Record.amount), else_=0)),
        0,
    )
    expense_expr = func.coalesce(
        func.sum(case((Record.type == "expense", Record.amount), else_=0)),
        0,
    )

    if use_daily:
        day_bucket = func.date(Record.date)
        rows_query = (
            q.with_entities(
                day_bucket.label("bucket"),
                income_expr.label("income_sum"),
                expense_expr.label("expense_sum"),
            )
            .group_by(day_bucket)
        )
        rows = rows_query.order_by(day_bucket.asc()).all()
        return [
            {
                "date": _format_bucket_date(b),
                "income": float(income_sum),
                "expense": float(expense_sum),
            }
            for b, income_sum, expense_sum in rows
        ]

    month_expr = func.strftime("%Y-%m", Record.date)
    rows_query = (
        q.with_entities(
            month_expr.label("month"),
            income_expr.label("income_sum"),
            expense_expr.label("expense_sum"),
        )
        .group_by(month_expr)
    )
    rows = rows_query.order_by(month_expr.asc()).all()
    return [
        {
            "month": month,
            "income": float(income_sum),
            "expense": float(expense_sum),
        }
        for month, income_sum, expense_sum in rows
    ]


def get_recent_activity(
    db: Session,
    current_user: Any,
    *,
    limit: int = 10,
) -> list[dict[str, Any]]:
    """
    Recent activity returns a *projected* view (not ORM objects).
    """
    q = _base_query(db, current_user)

    rows = (
        q.with_entities(
            Record.id,
            Record.amount,
            Record.type,
            Record.category,
            Record.sub_category,
            Record.date,
            Record.notes,
            Record.currency,
        )
        .order_by(Record.date.desc(), Record.id.desc())
        .limit(limit)
        .all()
    )

    return [
        {
            "id": rid,
            "amount": float(amount),
            "type": rtype,
            "category": category,
            "sub_category": sub_category,
            "date": rdate.isoformat() if rdate else None,
            "notes": notes,
            "currency": currency,
        }
        for rid, amount, rtype, category, sub_category, rdate, notes, currency in rows
    ]