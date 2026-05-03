from sqlalchemy import Column, ForeignKey, Integer, String, JSON
from app.db.database import Base


class TestTemplate(Base):
    __tablename__ = "test_templates"

    id = Column(Integer, primary_key=True, index=True)
    created_by_user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    name = Column(String, nullable=False)
    parameters = Column(JSON, nullable=False)
