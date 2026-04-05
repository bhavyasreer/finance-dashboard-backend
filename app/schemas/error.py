"""
OpenAPI error response models — one schema per HTTP status so Swagger shows
context-appropriate examples (not a single shared sample for every code).
"""

from pydantic import BaseModel, ConfigDict


class ApiErrorResponse(BaseModel):
    """Shared shape: ``{ "error", "message" }`` (no default example)."""

    error: str
    message: str


class BadRequestErrorResponse(ApiErrorResponse):
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "error": "BAD_REQUEST",
                "message": "Invalid request parameters",
            }
        }
    )


class UnauthorizedErrorResponse(ApiErrorResponse):
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "error": "UNAUTHORIZED",
                "message": "Invalid or missing authentication token",
            }
        }
    )


class ForbiddenErrorResponse(ApiErrorResponse):
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "error": "FORBIDDEN",
                "message": "You do not have permission to perform this action",
            }
        }
    )


class NotFoundErrorResponse(ApiErrorResponse):
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "error": "NOT_FOUND",
                "message": "Requested resource not found",
            }
        }
    )


class ValidationErrorResponse(ApiErrorResponse):
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "error": "VALIDATION_ERROR",
                "message": "Password must be at least 8 characters",
            }
        }
    )


class InternalServerErrorResponse(ApiErrorResponse):
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "error": "INTERNAL_SERVER_ERROR",
                "message": "Something went wrong",
            }
        }
    )
