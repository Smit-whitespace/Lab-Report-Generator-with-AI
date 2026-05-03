from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db.database import SessionLocal
from app.models.hospital import Hospital
from app.models.test_record import TestRecord
from app.models.test_template import TestTemplate
from app.schemas.test_record import TestRecordCreate, TestRecordResponse
from app.core.audit import log_action
from app.core.ai import generate_summary, standard_summary
from app.core.settings import get_system_settings
from fastapi.responses import FileResponse
from app.core.pdf import generate_pdf
from app.api.routes.auth import require_roles
from datetime import datetime

router = APIRouter()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.post("/", response_model=TestRecordResponse)
def create_record(
    record: TestRecordCreate,
    db: Session = Depends(get_db),
    current_user=Depends(require_roles("technician")),
):

    template = db.query(TestTemplate).filter(TestTemplate.id == record.template_id).first()
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")

    # Extract allowed parameter names
    allowed_params = {param["name"] for param in template.parameters}

    # Incoming parameters
    incoming_params = set(record.results.keys())

    # Check for extra fields
    extra_fields = incoming_params - allowed_params
    if extra_fields:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid parameters: {list(extra_fields)}"
        )

    # Check for missing fields
    missing_fields = allowed_params - incoming_params
    if missing_fields:
        raise HTTPException(
            status_code=400,
            detail=f"Missing parameters: {list(missing_fields)}"
        )

    created_at = datetime.now()

    db_record = TestRecord(
        template_id=record.template_id,
        created_by_user_id=current_user.id,
        patient_name=record.patient_name,
        patient_age=record.patient_age,
        patient_gender=record.patient_gender,
        patient_phone=record.patient_phone,
        referring_doctor=record.referring_doctor,
        results=record.results,
        created_at=created_at.strftime("%Y-%m-%d %H:%M:%S")
    )

    db.add(db_record)
    db.flush()
    db_record.report_number = f"LR-{created_at:%Y%m%d}-{db_record.id:04d}"
    log_action(
        db=db,
        action="create_record",
        entity_type="test_record",
        entity_id=db_record.id,
        user_id=current_user.id,
        details={"report_number": db_record.report_number},
    )
    db.commit()
    db.refresh(db_record)
    return db_record


@router.get("/", response_model=list[TestRecordResponse])
def get_records(
    db: Session = Depends(get_db),
    _current_user=Depends(require_roles("admin", "technician", "doctor")),
):
    return db.query(TestRecord).all()


@router.get("/{record_id}", response_model=TestRecordResponse)
def get_record(
    record_id: int,
    db: Session = Depends(get_db),
    _current_user=Depends(require_roles("admin", "technician", "doctor")),
):
    record = db.query(TestRecord).filter(TestRecord.id == record_id).first()
    if not record:
        raise HTTPException(status_code=404, detail="Record not found")

    return record


@router.get("/{record_id}/summary")
def get_summary(
    record_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(require_roles("admin", "technician", "doctor")),
):

    record = db.query(TestRecord).filter(TestRecord.id == record_id).first()
    if not record:
        raise HTTPException(status_code=404, detail="Record not found")

    template = db.query(TestTemplate).filter(TestTemplate.id == record.template_id).first()
    settings = get_system_settings(db)

    if not settings.ai_summary_enabled:
        return {
            "record_id": record.id,
            "summary": standard_summary(template.name, record.results),
            "source": "ai_disabled"
        }

    if record.summary:
        return {
            "record_id": record.id,
            "summary": record.summary,
            "source": "cached"
        }

    summary = generate_summary(template.name, record.results)

    record.summary = summary
    log_action(
        db=db,
        action="generate_summary",
        entity_type="test_record",
        entity_id=record.id,
        user_id=current_user.id,
        details={"source": "generated"},
    )
    db.commit()

    return {
        "record_id": record.id,
        "summary": summary,
        "source": "generated"
    }

@router.post("/{record_id}/regenerate-summary")
def regenerate_summary(
    record_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(require_roles("admin", "technician")),
):

    record = db.query(TestRecord).filter(TestRecord.id == record_id).first()
    if not record:
        raise HTTPException(status_code=404, detail="Record not found")

    template = db.query(TestTemplate).filter(TestTemplate.id == record.template_id).first()
    settings = get_system_settings(db)
    if not settings.ai_summary_enabled:
        raise HTTPException(status_code=400, detail="AI summary generation is disabled")

    # Force regenerate
    summary = generate_summary(template.name, record.results)

    record.summary = summary
    log_action(
        db=db,
        action="regenerate_summary",
        entity_type="test_record",
        entity_id=record.id,
        user_id=current_user.id,
        details={"source": "regenerated"},
    )
    db.commit()

    return {
        "record_id": record.id,
        "summary": summary,
        "source": "regenerated"
    }

@router.get("/{record_id}/pdf")
def generate_report_pdf(
    record_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(require_roles("admin", "technician", "doctor")),
):

    record = db.query(TestRecord).filter(TestRecord.id == record_id).first()
    if not record:
        raise HTTPException(status_code=404, detail="Record not found")

    template = db.query(TestTemplate).filter(TestTemplate.id == record.template_id).first()
    hospital = db.query(Hospital).order_by(Hospital.id.asc()).first()

    file_path = f"report_{record.report_number or record.id}.pdf"

    generate_pdf(
        file_path=file_path,
        hospital_profile={
            "name": hospital.name,
            "address": hospital.address,
            "phone": hospital.phone,
            "email": hospital.email,
            "registration_number": hospital.registration_number,
        } if hospital else None,
        report_number=record.report_number,
        template_name=template.name,
        patient_name=record.patient_name,
        patient_age=record.patient_age,
        patient_gender=record.patient_gender,
        patient_phone=record.patient_phone,
        referring_doctor=record.referring_doctor,
        created_at=record.created_at,
        results=record.results,
        parameters=template.parameters,
    )

    log_action(
        db=db,
        action="download_pdf",
        entity_type="test_record",
        entity_id=record.id,
        user_id=current_user.id,
        details={"report_number": record.report_number},
    )
    db.commit()

    return FileResponse(path=file_path, filename=file_path, media_type='application/pdf')
