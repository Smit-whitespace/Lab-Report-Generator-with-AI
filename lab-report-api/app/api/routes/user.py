from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db.database import SessionLocal
from app.models.audit_log import AuditLog
from app.models.test_record import TestRecord
from app.models.test_template import TestTemplate
from app.models.user import User
from app.schemas.user import UserCreate, UserResponse, UserUpdate
from app.core.audit import log_action
from app.core.security import hash_password
from app.api.routes.auth import require_roles

router = APIRouter()
DELETE_USER_CONFIRM_TEXT = "DELETE USER"
PROTECTED_SUPER_ADMIN_USERNAMES = {"supa admin", "supa_admin"}
PROTECTED_SUPER_ADMIN_NAMES = {"super admin", "supa admin"}

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def save_user(
    user: UserCreate,
    db: Session,
    actor_user_id: int | None,
    action: str,
) -> User:
    existing_username = db.query(User).filter(User.username == user.username).first()
    if existing_username:
        raise HTTPException(status_code=400, detail="Username already registered")

    existing_user = db.query(User).filter(User.email == user.email).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")

    db_user = User(
        name=user.name,
        username=user.username,
        email=user.email,
        password_hash=hash_password(user.password),
        role=user.role.value
    )

    db.add(db_user)
    db.flush()
    log_action(
        db=db,
        action=action,
        entity_type="user",
        entity_id=db_user.id,
        user_id=actor_user_id,
        details={"username": db_user.username, "role": db_user.role},
    )
    db.commit()
    db.refresh(db_user)
    return db_user


def is_protected_super_admin(user: User) -> bool:
    username = (user.username or "").strip().lower()
    name = (user.name or "").strip().lower()
    return (
        username in PROTECTED_SUPER_ADMIN_USERNAMES
        or name in PROTECTED_SUPER_ADMIN_NAMES
    )


@router.post("/bootstrap-admin", response_model=UserResponse)
def bootstrap_admin(user: UserCreate, db: Session = Depends(get_db)):
    existing_user_count = db.query(User).count()
    if existing_user_count > 0:
        raise HTTPException(status_code=400, detail="Bootstrap admin already created")

    if user.role.value != "admin":
        raise HTTPException(status_code=400, detail="First user must be an admin")

    return save_user(
        user=user,
        db=db,
        actor_user_id=None,
        action="bootstrap_admin",
    )


@router.post("/", response_model=UserResponse)
def create_user(
    user: UserCreate,
    db: Session = Depends(get_db),
    current_user=Depends(require_roles("admin")),
):
    return save_user(
        user=user,
        db=db,
        actor_user_id=current_user.id,
        action="create_user",
    )


@router.get("/", response_model=list[UserResponse])
def get_users(
    db: Session = Depends(get_db),
    _current_user=Depends(require_roles("admin")),
):
    return db.query(User).all()


@router.put("/{user_id}", response_model=UserResponse)
def update_user(
    user_id: int,
    user_update: UserUpdate,
    db: Session = Depends(get_db),
    current_user=Depends(require_roles("admin")),
):
    db_user = db.query(User).filter(User.id == user_id).first()
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")

    if user_update.username and user_update.username != db_user.username:
        existing_username = (
            db.query(User)
            .filter(User.username == user_update.username)
            .first()
        )
        if existing_username:
            raise HTTPException(status_code=400, detail="Username already registered")
        db_user.username = user_update.username

    if user_update.email and user_update.email != db_user.email:
        existing_email = db.query(User).filter(User.email == user_update.email).first()
        if existing_email:
            raise HTTPException(status_code=400, detail="Email already registered")
        db_user.email = user_update.email

    if user_update.name is not None:
        db_user.name = user_update.name
    if user_update.password is not None:
        db_user.password_hash = hash_password(user_update.password)
    if user_update.role is not None:
        db_user.role = user_update.role.value

    log_action(
        db=db,
        action="update_user",
        entity_type="user",
        entity_id=db_user.id,
        user_id=current_user.id,
        details={"username": db_user.username, "role": db_user.role},
    )
    db.commit()
    db.refresh(db_user)
    return db_user


@router.delete("/{user_id}")
def delete_user(
    user_id: int,
    confirm_text: str,
    db: Session = Depends(get_db),
    current_user=Depends(require_roles("admin")),
):
    if confirm_text != DELETE_USER_CONFIRM_TEXT:
        raise HTTPException(
            status_code=400,
            detail=f"Type {DELETE_USER_CONFIRM_TEXT} to confirm user deletion",
        )

    db_user = db.query(User).filter(User.id == user_id).first()
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")

    if is_protected_super_admin(db_user):
        raise HTTPException(status_code=400, detail="Supa admin cannot be deleted")

    if db_user.id == current_user.id:
        raise HTTPException(status_code=400, detail="You cannot delete your own active account")

    db.query(TestRecord).filter(TestRecord.created_by_user_id == db_user.id).update(
        {TestRecord.created_by_user_id: None}
    )
    db.query(TestTemplate).filter(TestTemplate.created_by_user_id == db_user.id).update(
        {TestTemplate.created_by_user_id: None}
    )
    db.query(AuditLog).filter(AuditLog.user_id == db_user.id).update(
        {AuditLog.user_id: None}
    )

    log_action(
        db=db,
        action="delete_user",
        entity_type="user",
        entity_id=db_user.id,
        user_id=current_user.id,
        details={"username": db_user.username, "role": db_user.role},
    )
    db.delete(db_user)
    db.commit()

    return {"message": "User deleted"}
