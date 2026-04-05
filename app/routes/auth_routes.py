from __future__ import annotations

import json
from urllib.parse import parse_qs

from fastapi import APIRouter, Depends, Request, status
from pydantic import BaseModel, ConfigDict, Field

from app.core.auth import create_access_token, raise_api_error, verify_password
from app.db.database import get_db
from app.models.user import User

router = APIRouter()


class LoginResponse(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxIn0.signature",
                "token_type": "bearer",
                "message": "Login successful",
            }
        }
    )

    access_token: str
    token_type: str = Field(default="bearer", examples=["bearer"])
    message: str = Field(default="Login successful")


_LOGIN_OPENAPI_EXTRA = {
    "requestBody": {
        "required": True,
        "content": {
            "application/json": {
                "schema": {
                    "type": "object",
                    "required": ["email", "password"],
                    "properties": {
                        "email": {"type": "string", "format": "email"},
                        "password": {"type": "string", "format": "password"},
                    },
                },
                "examples": {
                    "bootstrap_admin": {
                        "summary": "Default bootstrap admin",
                        "value": {
                            "email": "admin@gmail.com",
                            "password": "admin123456",
                        },
                    },
                },
            },
            "application/x-www-form-urlencoded": {
                "schema": {
                    "type": "object",
                    "properties": {
                        "username": {
                            "type": "string",
                            "description": "Email address (OAuth2 password flow compatibility)",
                        },
                        "password": {"type": "string"},
                    },
                    "required": ["username", "password"],
                }
            },
        },
    },
}


@router.post(
    "/login",
    response_model=LoginResponse,
    summary="Login",
    description=(
        "Authenticate with **email** and **password**; copy **access_token** from the response. "
        "Then click **Authorize** at the top of Swagger: you will see **HTTPBearer** with one value field — "
        "paste the JWT there (no `Bearer ` prefix; Swagger adds it).\\n\\n"
        "**Request body:** JSON `{\"email\",\"password\"}` ."
    ),
    openapi_extra=_LOGIN_OPENAPI_EXTRA,
)
async def login(request: Request, db=Depends(get_db)) -> LoginResponse:
    """
    Accepts:
    - JSON: `{"email":"...","password":"..."}` (`Content-Type: application/json`)
    - Form: `username` + `password` for `application/x-www-form-urlencoded`
    """
    body_bytes = await request.body()
    raw_ct = request.headers.get("content-type") or ""
    content_type = raw_ct.split(";")[0].strip().lower()

    email = ""
    password = ""

    if not body_bytes.strip():
        raise_api_error(
            status.HTTP_400_BAD_REQUEST,
            "BAD_REQUEST",
            "Request body is required. In Swagger, set request body to JSON, e.g. "
            '{"email":"admin@gmail.com","password":"your-password"} '
            "(media type application/json).",
        )

    is_form = content_type == "application/x-www-form-urlencoded"
    looks_like_form = b"=" in body_bytes and not body_bytes.lstrip().startswith((b"{", b"["))

    if is_form or (not content_type and looks_like_form):
        try:
            raw = body_bytes.decode("utf-8")
        except UnicodeDecodeError:
            raise_api_error(
                status.HTTP_400_BAD_REQUEST,
                "BAD_REQUEST",
                "Request body must be valid UTF-8",
            )
        form = parse_qs(raw)
        email = (form.get("username", [""])[0] or form.get("email", [""])[0] or "").strip()
        password = form.get("password", [""])[0] or ""
    else:
        try:
            body = json.loads(body_bytes.decode("utf-8"))
        except (json.JSONDecodeError, UnicodeDecodeError):
            raise_api_error(
                status.HTTP_400_BAD_REQUEST,
                "BAD_REQUEST",
                "Request body must be a JSON object with email and password, "
                "or use application/x-www-form-urlencoded with username and password.",
            )
        if not isinstance(body, dict):
            raise_api_error(
                status.HTTP_400_BAD_REQUEST,
                "BAD_REQUEST",
                "Request body must be a JSON object",
            )
        email = (body.get("email") or "").strip()
        password = body.get("password") if body.get("password") is not None else ""
        if not isinstance(password, str):
            password = str(password)

    if not email:
        raise_api_error(
            status.HTTP_422_UNPROCESSABLE_CONTENT,
            "VALIDATION_ERROR",
            "Email is required",
        )
    if not password:
        raise_api_error(
            status.HTTP_422_UNPROCESSABLE_CONTENT,
            "VALIDATION_ERROR",
            "Password is required",
        )

    user = db.query(User).filter(User.email == email).first()
    if not user:
        raise_api_error(
            status.HTTP_401_UNAUTHORIZED,
            "UNAUTHORIZED",
            "Invalid email or password",
        )

    if not user.password:
        raise_api_error(
            status.HTTP_401_UNAUTHORIZED,
            "UNAUTHORIZED",
            "Invalid email or password",
        )

    if not verify_password(password, user.password):
        raise_api_error(
            status.HTTP_401_UNAUTHORIZED,
            "UNAUTHORIZED",
            "Invalid email or password",
        )

    if not user.is_active:
        raise_api_error(
            status.HTTP_403_FORBIDDEN,
            "USER_INACTIVE",
            "User account is deactivated. Please contact admin.",
        )

    access_token = create_access_token({"user_id": user.id, "role": user.role})
    return LoginResponse(access_token=access_token, message="Login successful")
