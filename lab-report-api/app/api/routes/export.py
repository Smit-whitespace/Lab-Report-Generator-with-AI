from datetime import datetime
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.api.routes.auth import require_roles
from app.core.audit import log_action
from app.db.database import SessionLocal
from app.models.test_record import TestRecord
from app.models.test_template import TestTemplate

router = APIRouter()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.get("/records")
def export_records(
    db: Session = Depends(get_db),
    current_user=Depends(require_roles("admin")),
):
    records = db.query(TestRecord).all()
    templates = {
        template.id: template.name
        for template in db.query(TestTemplate).all()
    }

    log_action(
        db=db,
        action="export_records",
        entity_type="test_record",
        user_id=current_user.id,
        details={"count": len(records)},
    )
    db.commit()

    return {
        "exported_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "count": len(records),
        "records": [
            {
                "id": record.id,
                "report_number": record.report_number,
                "template_id": record.template_id,
                "template_name": templates.get(record.template_id),
                "created_by_user_id": record.created_by_user_id,
                "patient_name": record.patient_name,
                "patient_age": record.patient_age,
                "patient_gender": record.patient_gender,
                "patient_phone": record.patient_phone,
                "referring_doctor": record.referring_doctor,
                "results": record.results,
                "summary": record.summary,
                "created_at": record.created_at,
            }
            for record in records
        ],
    }


@router.get("/database")
def export_database(
    db: Session = Depends(get_db),
    current_user=Depends(require_roles("admin")),
):
    database_path = Path("lab_reports.db")
    if not database_path.exists():
        raise HTTPException(status_code=404, detail="Database file not found")

    log_action(
        db=db,
        action="backup_database",
        entity_type="database",
        user_id=current_user.id,
        details={"file": str(database_path)},
    )
    db.commit()

    filename = f"lab_reports_backup_{datetime.now():%Y%m%d_%H%M%S}.db"
    return FileResponse(
        path=str(database_path),
        filename=filename,
        media_type="application/octet-stream",
    )
