from sqlalchemy import Boolean, Column, Integer

from app.db.database import Base


class SystemSetting(Base):
    __tablename__ = "system_settings"

    id = Column(Integer, primary_key=True, index=True)
    ai_summary_enabled = Column(Boolean, nullable=False, default=False)
