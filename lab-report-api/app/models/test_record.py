from sqlalchemy import Column, Integer, JSON, ForeignKey, Text, String
from app.db.database import Base


class TestRecord(Base):
    __tablename__ = "test_records"

    id = Column(Integer, primary_key=True, index=True)
    report_number = Column(String, unique=True, index=True, nullable=True)
    template_id = Column(Integer, ForeignKey("test_templates.id"))
    created_by_user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    results = Column(JSON, nullable=False)
    summary = Column(Text, nullable=True)
    patient_name = Column(String, nullable=False)
    patient_age = Column(Integer, nullable=False)
    patient_gender = Column(String, nullable=False)
    patient_phone = Column(String, nullable=True)
    referring_doctor = Column(String, nullable=True)
    created_at = Column(String, nullable=True)
