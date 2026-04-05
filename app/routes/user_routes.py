from typing import Literal

from fastapi import APIRouter, Depends, Query

from app.core.auth import require_permission
from app.db.database import get_db
from app.schemas.user import UserCreate, UserCreatedOut, UserDeactivate, UserOut, UserRoleUpdate
from app.services.user_service import create_user, deactivate_user, get_users, update_user_role

router = APIRouter()


@router.post("/", summary="Create User", description="Create a new user with default role as viewer.")
def create(
    user: UserCreate,
    db=Depends(get_db),
    _: object = Depends(require_permission("MANAGE_USERS")),
) -> UserCreatedOut:
    u = create_user(db, user)
    return UserCreatedOut.model_validate(u)


@router.get(
    "/",
    summary="List Users",
    description=(
        "Admins can filter by ``role`` and ``is_active``, and use ``search`` for a case-insensitive "
        "substring on **name** or **email** (OR within search). All parameters are combined with **AND**. "
        "Example: ``GET /users?search=john&role=admin&is_active=true``."
    ),
    response_model=list[UserOut],
)
def list_users(
    db=Depends(get_db),
    _: object = Depends(require_permission("MANAGE_USERS")),
    is_active: bool | None = Query(
        None,
        description="If set, return only users with this active status.",
    ),
    role: Literal["viewer", "analyst", "admin"] | None = Query(
        None,
        description="If set, return only users with this role.",
    ),
    search: str | None = Query(
        None,
        description="Case-insensitive partial match on name or email.",
    ),
):
    return get_users(db, is_active=is_active, role=role, search=search)

@router.patch("/{id}", summary="Activate/Deactivate User", description="Toggle user active status.")
def deactivate(
    id: int,
    payload: UserDeactivate,
    db=Depends(get_db),
    _: object = Depends(require_permission("MANAGE_USERS")),
) -> UserOut:
    return deactivate_user(db, id, is_active=payload.is_active)


@router.patch("/{id}/role", summary="Update User Role", description="Assign or update user role (viewer, analyst, admin).")
def update_role(
    id: int,
    payload: UserRoleUpdate,
    db=Depends(get_db),
    _: object = Depends(require_permission("MANAGE_USERS")),
) -> UserOut:
    return update_user_role(db, id, role=payload.role)