from __future__ import annotations

from datetime import datetime
from typing import Literal

from email_validator import EmailNotValidError, validate_email
from pydantic import BaseModel, ConfigDict, Field, field_validator

UserRole = Literal["viewer", "analyst", "admin"]


class UserCreate(BaseModel):
    """
    Public user creation payload for admins.
    Role is NOT accepted from the client; users default to `viewer`.
    """

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "name": "Jane Analyst",
                "email": "jane@example.com",
                "password": "securepass123",
            }
        }
    )

    name: str = Field(max_length=255)
    email: str = Field(max_length=320)
    password: str = Field(max_length=128)

    @field_validator("name")
    @classmethod
    def name_required(cls, value: str) -> str:
        s = value.strip() if isinstance(value, str) else ""
        if not s:
            raise ValueError("Field required")
        return s

    @field_validator("email")
    @classmethod
    def validate_email_format(cls, value: str) -> str:
        s = value.strip() if isinstance(value, str) else ""
        if not s:
            raise ValueError("Field required")
        try:
            validate_email(s, check_deliverability=False)
        except EmailNotValidError:
            raise ValueError("Email must be valid")
        return s

    @field_validator("password")
    @classmethod
    def validate_password(cls, value: str) -> str:
        if not isinstance(value, str) or not value.strip():
            raise ValueError("Field required")
        if len(value) < 8:
            raise ValueError("Password must be at least 8 characters")
        return value


class UserDeactivate(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={"example": {"is_active": False}}
    )

    is_active: bool


class UserRoleUpdate(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={"example": {"role": "analyst"}}
    )

    role: UserRole


_USER_OUT_EXAMPLE: dict = {
    "id": 1,
    "name": "Sample User",
    "email": "user@example.com",
    "role": "viewer",
    "is_active": True,
    "created_at": "2026-04-01T10:00:00+00:00",
}


class UserOut(BaseModel):
    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={"example": _USER_OUT_EXAMPLE},
    )

    id: int
    name: str
    email: str
    role: UserRole
    is_active: bool
    created_at: datetime


class UserCreatedOut(UserOut):
    """Same fields as ``UserOut`` plus a success message (create user only)."""

    message: str = Field(default="User created successfully")

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                **_USER_OUT_EXAMPLE,
                "message": "User created successfully",
            }
        },
    )
