from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from backend.app.api.deps import ensure_plan_exists, resolve_demo_plan
from backend.app.database import get_db
from backend.app.schemas.catalog import AccessCurrentResponse, AccessPlanResponse
from backend.app.services import access_control as access_service
from backend.app.services import catalog as catalog_service

router = APIRouter()


@router.get("/access/plans", response_model=list[AccessPlanResponse])
def access_plans(db: Session = Depends(get_db)) -> list[AccessPlanResponse]:
    return [
        AccessPlanResponse(id=plan.id, name=plan.name, history_days=plan.history_days)
        for plan in access_service.list_access_plans(db)
    ]


@router.get("/access/current", response_model=AccessCurrentResponse)
def access_current(
    plan: str = Depends(resolve_demo_plan),
    db: Session = Depends(get_db),
) -> AccessCurrentResponse:
    ensure_plan_exists(db, plan)
    catalog_plan = access_service.get_plan(db, plan)
    reference_latest = catalog_service.latest_timestamp(db, "mrms_reflectivity")
    history_days = access_service.get_history_limit_days(db, plan)

    return AccessCurrentResponse(
        plan=plan,
        name=catalog_plan.name if catalog_plan else plan,
        history_days=history_days,
        history_limit_label=access_service.history_limit_label(history_days),
        reference_latest=reference_latest,
        demo_mode=True,
        upgrade_message=access_service.upgrade_message_for_plan(plan),
    )
