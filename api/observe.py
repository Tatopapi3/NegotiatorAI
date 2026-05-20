from fastapi import APIRouter
from core.observability import get_dashboard_stats

router = APIRouter(prefix="/observe", tags=["observability"])


@router.get("/stats", summary="Observability dashboard data")
def stats():
    return get_dashboard_stats()
