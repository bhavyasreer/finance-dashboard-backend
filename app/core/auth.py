from __future__ import annotations

import os
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Callable, FrozenSet, Any

import bcrypt
from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import jwt
from jose.exceptions import ExpiredSignatureError, JWTError
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.models.record import Record
from app.models.user import User

# Permission-based RBAC mapping.
ROLE_PERMISSIONS: dict[str, list[str]] = {
    "viewer": ["VIEW_DASHBOARD"],
    "analyst": [
        "VIEW_DASHBOARD",
        "VIEW_RECORDS",
    ],
    "admin": [
        "VIEW_DASHBOARD",
        "VIEW_RECORDS",
        "CREATE_RECORDS",
        "UPDATE_RECORDS",
        "DELETE_RECORDS",
        "MANAGE_USERS",
    ],
}

JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY") or os.getenv("SECRET_KEY", "dev-secret-change-me")
JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("JWT_EXPIRE_MINUTES", "60"))  # 1 hour default

_BEARER_WWW_AUTH = {"WWW-Authenticate": "Bearer"}

# HTTP Bearer in OpenAPI/Swagger: single field to paste the JWT from POST /auth/login.
# (OAuth2PasswordBearer would show username/password and target tokenUrl — not what we want after login.)
http_bearer_scheme = HTTPBearer(auto_error=False)


def raise_api_error(
    status_code: int,
    error_code: str,
    message: str,
    *,
    headers: dict[str, str] | None = None,
) -> None:
    raise HTTPException(
        status_code=status_code,
        detail={"error": error_code, "message": message},
        headers=headers,
    )


@dataclass(frozen=True)
class AuthUser:
    id: int
    role: str
    is_active: bool


def _role_permissions(role: str) -> FrozenSet[str]:
    return frozenset(ROLE_PERMISSIONS.get(role, []))


def hash_password(password: str) -> str:
    hashed = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt())
    return hashed.decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    try:
        return bcrypt.checkpw(plain_password.encode("utf-8"), hashed_password.encode("utf-8"))
    except Exception:
        return False


def create_access_token(data: dict) -> str:
    to_encode = {**data}
    expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode["exp"] = expire
    return jwt.encode(to_encode, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)


def get_current_user(
    request: Request,
    credentials: HTTPAuthorizationCredentials | None = Depends(http_bearer_scheme),
    db: Session = Depends(get_db),
) -> AuthUser:
    """
    Reads ``Authorization: Bearer <JWT>``, decodes it, loads the user from the DB, returns AuthUser.
    Attaches a small user payload on ``request.state.user`` for downstream use.
    """
    if credentials is None or not credentials.credentials:
        raise_api_error(
            status.HTTP_401_UNAUTHORIZED,
            "UNAUTHORIZED",
            "Invalid or missing authentication token",
            headers=_BEARER_WWW_AUTH,
        )
    token = credentials.credentials.strip()
    try:
        payload: dict[str, Any] = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
    except ExpiredSignatureError:
        raise_api_error(
            status.HTTP_401_UNAUTHORIZED,
            "UNAUTHORIZED",
            "Invalid or expired token",
            headers=_BEARER_WWW_AUTH,
        )
    except JWTError:
        raise_api_error(
            status.HTTP_401_UNAUTHORIZED,
            "UNAUTHORIZED",
            "Invalid or expired token",
            headers=_BEARER_WWW_AUTH,
        )

    user_id = payload.get("user_id")
    role = payload.get("role")
    if user_id is None:
        raise_api_error(
            status.HTTP_401_UNAUTHORIZED,
            "UNAUTHORIZED",
            "Invalid or expired token",
            headers=_BEARER_WWW_AUTH,
        )

    try:
        uid = int(user_id)
    except (TypeError, ValueError):
        raise_api_error(
            status.HTTP_401_UNAUTHORIZED,
            "UNAUTHORIZED",
            "Invalid or expired token",
            headers=_BEARER_WWW_AUTH,
        )

    user = db.query(User).filter(User.id == uid).first()
    if not user:
        raise_api_error(
            status.HTTP_401_UNAUTHORIZED,
            "UNAUTHORIZED",
            "Invalid or expired token",
            headers=_BEARER_WWW_AUTH,
        )

    if not user.is_active:
        raise_api_error(
            status.HTTP_403_FORBIDDEN,
            "USER_INACTIVE",
            "User is inactive and cannot access the system.",
        )

    auth_user = AuthUser(id=user.id, role=user.role if user.role else (role or ""), is_active=bool(user.is_active))
    request.state.user = {"id": auth_user.id, "role": auth_user.role, "is_active": auth_user.is_active}

    return auth_user


def require_permission(permission: str) -> Callable[[AuthUser], AuthUser]:
    """
    Reusable permission dependency.
    Raises HTTP 403 for unauthorized actions.
    """

    def checker(current_user: AuthUser = Depends(get_current_user)) -> AuthUser:
        if permission not in _role_permissions(current_user.role):
            raise_api_error(
                status.HTTP_403_FORBIDDEN,
                "FORBIDDEN",
                "Access denied for this role",
            )

        return current_user

    return checker


def require_record_ownership_or_admin(
    id: int,
    db: Session = Depends(get_db),
    current_user: AuthUser = Depends(get_current_user),
) -> Record:
    """
    Ownership logic for record updates/deletes.
    Non-admin users can modify only their own records.
    """
    record = (
        db.query(Record)
        .filter(Record.id == id, Record.is_deleted.is_(False))
        .first()
    )
    if not record:
        raise_api_error(
            status.HTTP_404_NOT_FOUND,
            "RECORD_NOT_FOUND",
            f"Record with id {id} not found",
        )

    is_admin = "MANAGE_USERS" in _role_permissions(current_user.role)
    if not is_admin and record.user_id != current_user.id:
        raise_api_error(
            status.HTTP_403_FORBIDDEN,
            "FORBIDDEN",
            "Access denied for this role",
        )

    return record