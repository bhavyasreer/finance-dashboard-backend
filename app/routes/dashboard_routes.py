from datetime import date

from fastapi import APIRouter, Depends, Query

from app.core.auth import require_permission
from app.db.database import get_db
from app.schemas.dashboard import (
    CategoryBreakdownOut,
    DashboardSummaryOut,
    DashboardTrendsOut,
    RecentActivityOut,
)
from app.services.dashboard_service import (
    category_breakdown,
    get_monthly_trends,
    get_recent_activity,
    get_summary,
)

router = APIRouter()


@router.get(
    "/summary",
    summary="Get Financial Summary",
    description="Aggregate income, expense, net balance, and related KPIs.",
    response_model=DashboardSummaryOut,
)
def summary(
    db=Depends(get_db),
    current_user=Depends(require_permission("VIEW_DASHBOARD")),
):
    return get_summary(db, current_user)


@router.get(
    "/category-breakdown",
    summary="Get Category Breakdown",
    description="Totals grouped by category.",
    response_model=CategoryBreakdownOut,
)
def category_breakdown_route(
    db=Depends(get_db),
    current_user=Depends(require_permission("VIEW_DASHBOARD")),
):
    return category_breakdown(db, current_user)


@router.get(
    "/monthly-trends",
    summary="Income and expense trends",
    description="Daily buckets for short ranges; monthly buckets for longer ranges.",
    response_model=DashboardTrendsOut,
)
def monthly_trends(
    start_date: date | None = Query(None),
    end_date: date | None = Query(None),
    db=Depends(get_db),
    current_user=Depends(require_permission("VIEW_DASHBOARD")),
):
    return get_monthly_trends(db, current_user, start_date=start_date, end_date=end_date)


@router.get(
    "/recent",
    summary="Recent activity",
    description="Latest transactions (projected fields).",
    response_model=RecentActivityOut,
)
def recent(
    limit: int = Query(10, ge=1, le=50),
    db=Depends(get_db),
    current_user=Depends(require_permission("VIEW_DASHBOARD")),
):
    return get_recent_activity(db, current_user, limit=limit)