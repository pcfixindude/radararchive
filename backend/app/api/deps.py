from typing import Optional

from fastapi import Header, HTTPException, Query
from sqlalchemy.orm import Session

from backend.app.config import VALID_DEMO_PLANS, settings


def resolve_demo_plan(
    plan: Optional[str] = Query(None, description="Dev/demo plan id: free, basic, pro, business"),
    x_demo_plan: Optional[str] = Header(None, alias="X-Demo-Plan"),
) -> str:
    raw = (plan or x_demo_plan or settings.default_demo_plan).strip().lower()
    if raw not in VALID_DEMO_PLANS:
        raise HTTPException(
            status_code=400,
            detail={
                "error": "invalid_plan",
                "message": f"Unknown plan '{raw}'. Use one of: {', '.join(sorted(VALID_DEMO_PLANS))}.",
            },
        )
    return raw


def ensure_plan_exists(session: Session, plan_id: str) -> None:
    from backend.app.models import AccessPlan

    if session.get(AccessPlan, plan_id) is None:
        raise HTTPException(
            status_code=400,
            detail={
                "error": "invalid_plan",
                "message": f"Plan '{plan_id}' is not configured in the catalog database.",
            },
        )
