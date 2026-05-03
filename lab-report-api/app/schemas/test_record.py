from pydantic import BaseModel
from typing import Dict


class TestRecordCreate(BaseModel):
    template_id: int
    patient_name: str
    patient_age: int
    patient_gender: str
    patient_phone: str | None = None
    referring_doctor: str | None = None
    results: Dict[str, float]


class TestRecordResponse(BaseModel):
    id: int
    report_number: str | None
    template_id: int
    created_by_user_id: int | None
    patient_name: str
    patient_age: int
    patient_gender: str
    patient_phone: str | None
    referring_doctor: str | None
    created_at: str | None
    results: Dict[str, float]

    class Config:
        from_attributes = True
