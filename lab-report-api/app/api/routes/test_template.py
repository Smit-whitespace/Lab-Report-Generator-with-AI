from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db.database import SessionLocal
from app.models.test_record import TestRecord
from app.models.test_template import TestTemplate
from app.schemas.test_template import (
    TestTemplateCreate,
    TestTemplateResponse,
    TestTemplateUpdate,
)
from app.core.audit import log_action
from app.api.routes.auth import get_current_user, require_roles

router = APIRouter()
DELETE_TEMPLATE_CONFIRM_TEXT = "DELETE TEMPLATE"


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def can_manage_template(template: TestTemplate, current_user) -> bool:
    return (
        current_user.role == "admin"
        or template.created_by_user_id == current_user.id
    )


@router.post("/", response_model=TestTemplateResponse)
def create_template(
    template: TestTemplateCreate,
    db: Session = Depends(get_db),
    current_user=Depends(require_roles("admin")),
):
    db_template = TestTemplate(
        created_by_user_id=current_user.id,
        name=template.name,
        parameters=[p.dict() for p in template.parameters]
    )

    db.add(db_template)
    db.flush()
    log_action(
        db=db,
        action="create_template",
        entity_type="test_template",
        entity_id=db_template.id,
        user_id=current_user.id,
        details={"name": db_template.name},
    )
    db.commit()
    db.refresh(db_template)
    return db_template


@router.get("/", response_model=list[TestTemplateResponse])
def get_templates(
    db: Session = Depends(get_db),
    _current_user=Depends(require_roles("admin", "technician", "doctor")),
):
    return db.query(TestTemplate).all()


@router.get("/{template_id}", response_model=TestTemplateResponse)
def get_template(
    template_id: int,
    db: Session = Depends(get_db),
    _current_user=Depends(require_roles("admin", "technician", "doctor")),
):
    template = db.query(TestTemplate).filter(TestTemplate.id == template_id).first()
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")

    return template


@router.put("/{template_id}", response_model=TestTemplateResponse)
def update_template(
    template_id: int,
    template_update: TestTemplateUpdate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    template = db.query(TestTemplate).filter(TestTemplate.id == template_id).first()
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")

    if not can_manage_template(template, current_user):
        raise HTTPException(status_code=403, detail="You cannot edit this template")

    if template_update.name is not None:
        template.name = template_update.name
    if template_update.parameters is not None:
        template.parameters = [p.dict() for p in template_update.parameters]

    log_action(
        db=db,
        action="update_template",
        entity_type="test_template",
        entity_id=template.id,
        user_id=current_user.id,
        details={"name": template.name},
    )
    db.commit()
    db.refresh(template)
    return template


@router.delete("/{template_id}")
def delete_template(
    template_id: int,
    confirm_text: str,
    db: Session = Depends(get_db),
    current_user=Depends(require_roles("admin")),
):
    if confirm_text != DELETE_TEMPLATE_CONFIRM_TEXT:
        raise HTTPException(
            status_code=400,
            detail=f"Type {DELETE_TEMPLATE_CONFIRM_TEXT} to confirm template deletion",
        )

    template = db.query(TestTemplate).filter(TestTemplate.id == template_id).first()
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")

    existing_record = (
        db.query(TestRecord)
        .filter(TestRecord.template_id == template.id)
        .first()
    )
    if existing_record:
        raise HTTPException(
            status_code=400,
            detail="Cannot delete template because reports already use it",
        )

    log_action(
        db=db,
        action="delete_template",
        entity_type="test_template",
        entity_id=template.id,
        user_id=current_user.id,
        details={"name": template.name},
    )
    db.delete(template)
    db.commit()

    return {"message": "Template deleted"}
