from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.routes.auth import require_roles
from app.core.audit import log_action
from app.core.settings import get_system_settings
from app.db.database import SessionLocal
from app.schemas.setting import AISummarySettingResponse, AISummarySettingUpdate

router = APIRouter()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.get("/ai-summary", response_model=AISummarySettingResponse)
def get_ai_summary_setting(
    db: Session = Depends(get_db),
    _current_user=Depends(require_roles("admin", "technician", "doctor")),
):
    settings = get_system_settings(db)
    db.commit()
    return {"enabled": settings.ai_summary_enabled}


@router.put("/ai-summary", response_model=AISummarySettingResponse)
def update_ai_summary_setting(
    setting_update: AISummarySettingUpdate,
    db: Session = Depends(get_db),
    current_user=Depends(require_roles("admin")),
):
    settings = get_system_settings(db)
    settings.ai_summary_enabled = setting_update.enabled
    log_action(
        db=db,
        action="update_ai_summary_setting",
        entity_type="system_setting",
        entity_id=settings.id,
        user_id=current_user.id,
        details={"enabled": setting_update.enabled},
    )
    db.commit()
    db.refresh(settings)
    return {"enabled": settings.ai_summary_enabled}
