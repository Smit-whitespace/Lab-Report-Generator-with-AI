from sqlalchemy.orm import Session

from app.models.system_setting import SystemSetting


def get_system_settings(db: Session) -> SystemSetting:
    settings = db.query(SystemSetting).filter(SystemSetting.id == 1).first()
    if settings:
        return settings

    settings = SystemSetting(id=1, ai_summary_enabled=False)
    db.add(settings)
    db.flush()
    return settings
