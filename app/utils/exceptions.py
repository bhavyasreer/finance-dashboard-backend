from __future__ import annotations

import logging
from typing import Any

from fastapi import HTTPException, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

logger = logging.getLogger(__name__)

_SKIP_LOC_PREFIXES = frozenset({"body", "query", "path", "header", "cookie"})

# Starlette/FastAPI default ``HTTPException(detail=...)`` strings — replace with our defaults.
_GENERIC_HTTP_DETAIL: frozenset[str] = frozenset(
    {
        "Not Found",
        "Bad Request",
        "Unauthorized",
        "Forbidden",
        "Method Not Allowed",
        "Internal Server Error",
        "Not authenticated",
        "Could not validate credentials",
    }
)

# When ``HTTPException`` uses a plain string detail, map status → (error_code, default_message).
_FALLBACK_ERROR: dict[int, tuple[str, str]] = {
    status.HTTP_400_BAD_REQUEST: ("BAD_REQUEST", "Invalid request parameters"),
    status.HTTP_401_UNAUTHORIZED: (
        "UNAUTHORIZED",
        "Invalid or missing authentication token",
    ),
    status.HTTP_403_FORBIDDEN: (
        "FORBIDDEN",
        "You do not have permission to perform this action",
    ),
    status.HTTP_404_NOT_FOUND: ("NOT_FOUND", "Requested resource not found"),
    status.HTTP_500_INTERNAL_SERVER_ERROR: (
        "INTERNAL_SERVER_ERROR",
        "Something went wrong",
    ),
}


def _field_path_from_loc(loc: tuple[Any, ...]) -> str:
    parts: list[str] = []
    for item in loc:
        if isinstance(item, str) and item in _SKIP_LOC_PREFIXES:
            continue
        parts.append(str(item))
    return ".".join(parts) if parts else "request"


def _normalize_validation_msg(msg: str) -> str:
    if not msg:
        return ""
    prefixes = ("Value error, ", "value_error.")
    for p in prefixes:
        if msg.startswith(p):
            msg = msg[len(p) :]
            break
    return msg.strip()


def _validation_user_message(errors: list[dict[str, Any]]) -> str:
    if not errors:
        return "Invalid input data"
    first = errors[0]
    loc = first.get("loc") or ()
    field = _field_path_from_loc(tuple(loc))
    raw = str(first.get("msg", "")).strip()
    msg = _normalize_validation_msg(raw) or "Invalid input data"

    if field and field != "request":
        field_lc = field.lower().replace("_", " ")
        msg_lc = msg.lower()
        if field_lc in msg_lc or msg_lc.startswith(field_lc + " "):
            return msg
        return f"{field}: {msg}"
    return msg


def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    hdrs = dict(exc.headers) if exc.headers else None

    if isinstance(exc.detail, dict) and "error" in exc.detail and "message" in exc.detail:
        return JSONResponse(status_code=exc.status_code, content=exc.detail, headers=hdrs)

    code, default_message = _FALLBACK_ERROR.get(
        exc.status_code,
        ("HTTP_ERROR", "Request failed"),
    )
    detail = exc.detail
    if isinstance(detail, str) and detail.strip() and detail not in _GENERIC_HTTP_DETAIL:
        message = detail
    else:
        message = default_message

    return JSONResponse(
        status_code=exc.status_code,
        content={"error": code, "message": message},
        headers=hdrs,
    )


def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    errors = exc.errors()
    message = _validation_user_message(errors)
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
        content={
            "error": "VALIDATION_ERROR",
            "message": message,
        },
    )


def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    logger.exception("Unhandled error", exc_info=exc)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": "INTERNAL_SERVER_ERROR",
            "message": "Something went wrong",
        },
    )
