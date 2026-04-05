from __future__ import annotations

from sqlalchemy import func, or_
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.auth import hash_password, raise_api_error
from app.models.user import User


def create_user(db: Session, data) -> User:
    # New users are always `viewer` (role selection removed from request payload).
    user = User(
        name=data.name,
        email=data.email,
        role="viewer",
        is_active=True,
        password=hash_password(data.password),
    )
    db.add(user)
    try:
        db.commit()
        db.refresh(user)
        return user
    except IntegrityError:
        db.rollback()
        raise_api_error(400, "EMAIL_ALREADY_EXISTS", "A user with this email already exists")


def get_users(
    db: Session,
    *,
    is_active: bool | None = None,
    role: str | None = None,
    search: str | None = None,
) -> list[User]:
    """List users; ``search`` matches name OR email (partial, case-insensitive); filters combine with AND."""
    q = db.query(User)
    if is_active is not None:
        q = q.filter(User.is_active.is_(is_active))
    if role is not None and role.strip():
        q = q.filter(func.lower(User.role) == role.strip().lower())
    term = (search or "").strip()
    if term:
        pattern = f"%{term.lower()}%"
        q = q.filter(
            or_(
                func.lower(User.name).like(pattern),
                func.lower(User.email).like(pattern),
            )
        )
    return q.order_by(User.id).all()


def deactivate_user(db: Session, user_id: int, *, is_active: bool) -> User:
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise_api_error(404, "USER_NOT_FOUND", "User not found")
    user.is_active = is_active
    db.commit()
    db.refresh(user)
    return user


def update_user_role(db: Session, user_id: int, *, role: str) -> User:
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise_api_error(404, "USER_NOT_FOUND", "User not found")
    user.role = role
    db.commit()
    db.refresh(user)
    return user