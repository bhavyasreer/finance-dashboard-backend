from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from fastapi.exceptions import RequestValidationError

from app.bootstrap import ensure_bootstrap_admin
from app.db.database import Base, engine
from app.routes import auth_routes, dashboard_routes, record_routes, user_routes
from app.schemas.error import (
    BadRequestErrorResponse,
    ForbiddenErrorResponse,
    InternalServerErrorResponse,
    NotFoundErrorResponse,
    UnauthorizedErrorResponse,
    ValidationErrorResponse,
)
from app.utils.exceptions import (
    http_exception_handler,
    unhandled_exception_handler,
    validation_exception_handler,
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Import models so all tables are registered on Base.metadata before create_all.
    import app.models  # noqa: F401

    Base.metadata.create_all(bind=engine)
    ensure_bootstrap_admin()
    yield


app = FastAPI(
    lifespan=lifespan,
    title="Zorvyn Finance Backend API",
    description="""
🚀 Getting Started:

1. Login using:
   POST /auth/login
2. Copy the access_token from response
3. Click 'Authorize' (top right)
4. Paste:
   Bearer <your_token>
5. Now test all protected APIs

---

👤 Roles:
- Admin → Full access
- Analyst → Read records + dashboard
- Viewer → Dashboard only
""",
@app.get("/")
def root():
    return {"message": "API running", "docs": "/docs"}

    responses={
        400: {
            "description": "Bad request (e.g. invalid parameters or business rule violation)",
            "model": BadRequestErrorResponse,
        },
        401: {
            "description": "Missing or invalid authentication",
            "model": UnauthorizedErrorResponse,
        },
        403: {
            "description": "Authenticated but not allowed for this action",
            "model": ForbiddenErrorResponse,
        },
        404: {
            "description": "Resource not found",
            "model": NotFoundErrorResponse,
        },
        422: {
            "description": "Request body or query failed validation",
            "model": ValidationErrorResponse,
        },
        500: {
            "description": "Unexpected server error",
            "model": InternalServerErrorResponse,
        },
    },
)

# Register exception handlers (order: specific handlers first; global last)
app.add_exception_handler(HTTPException, http_exception_handler)
app.add_exception_handler(RequestValidationError, validation_exception_handler)
app.add_exception_handler(Exception, unhandled_exception_handler)

# Routers
app.include_router(user_routes.router, prefix="/users", tags=["Users"])
app.include_router(record_routes.router, prefix="/records", tags=["Records"])
app.include_router(dashboard_routes.router, prefix="/dashboard", tags=["Dashboard"])
app.include_router(auth_routes.router, prefix="/auth", tags=["Auth"])