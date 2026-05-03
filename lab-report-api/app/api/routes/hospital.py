from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.routes.auth import require_roles
from app.core.audit import log_action
from app.db.database import SessionLocal
from app.models.hospital import Hospital
from app.schemas.hospital import HospitalCreate, HospitalResponse

router = APIRouter()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.get("/profile", response_model=HospitalResponse)
def get_hospital_profile(
    db: Session = Depends(get_db),
    _current_user=Depends(require_roles("admin", "technician", "doctor")),
):
    hospital = db.query(Hospital).order_by(Hospital.id.asc()).first()
    if not hospital:
        raise HTTPException(status_code=404, detail="Hospital profile not created")

    return hospital


@router.put("/profile", response_model=HospitalResponse)
def upsert_hospital_profile(
    profile: HospitalCreate,
    db: Session = Depends(get_db),
    current_user=Depends(require_roles("admin")),
):
    hospital = db.query(Hospital).order_by(Hospital.id.asc()).first()
    action = "update_hospital"

    if not hospital:
        hospital = Hospital(
            name=profile.name,
            updated_at=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        )
        db.add(hospital)
        action = "create_hospital"

    hospital.name = profile.name
    hospital.address = profile.address
    hospital.phone = profile.phone
    hospital.email = profile.email
    hospital.registration_number = profile.registration_number
    hospital.updated_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    db.flush()
    log_action(
        db=db,
        action=action,
        entity_type="hospital",
        entity_id=hospital.id,
        user_id=current_user.id,
        details={"name": hospital.name},
    )
    db.commit()
    db.refresh(hospital)
    return hospital
