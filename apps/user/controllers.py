from apps.user.routers import user_router
from fastapi import APIRouter, Depends, HTTPException, Path, Form, status
from typing_extensions import Annotated
from utils.permissions import get_current_user, permission_required
from apps.user.repository import SessionDep
from utils.db_filler import seed_access_data
from apps.auth.services import ProtectionDep
from apps.user.models import UpdateUserSchema
from apps.user.schemas import User
from apps.user.repository import UserRepository


@user_router.post("/fill_db")
async def db_filler(session: SessionDep):
    await seed_access_data(session)


@user_router.get("/access-rules")
async def get_rules(user=Depends(get_current_user)):
    if user.role.name != "admin":
        raise HTTPException(403)
    return {"message": "list of access rules"}


# @user_router.get("/")
# async def products(user=Depends(permission_required("products", "read", session))):
#     return [{"id": 1, "name": "Laptop", "owner_id": 1}]


@user_router.patch("/{user_id}")
async def update_user(
    user_id: Annotated[int, Path(title="Идентификатор пользователя", ge=0, le=1000)],
    user: Annotated[UpdateUserSchema, Form()],
    session: SessionDep,
    protection: ProtectionDep,
):
    if (
        protection not in (1, 3)
    ):  # Здесь можно было бы добавить функционал получения списка ролей из БД путем отдельного запроса или запросить роли из Кэша. Не стал усложнять
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Отсутствуют необходимые права",
        )
    return await UserRepository.update_user(user_id, user, session)


@user_router.patch("/soft_del/{user_id}")
async def user_soft_delete(
    user_id: Annotated[int, Path(title="Идентификатор пользователя", ge=0, le=1000)],
    session: SessionDep,
    protection: ProtectionDep,
):
    if (
        protection not in (1, 3)
    ):  # Здесь можно было бы добавить функционал получения списка ролей из БД путем отдельного запроса или запросить роли из Кэша. Не стал усложнять
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Отсутствуют необходимые права",
        )
    return await UserRepository.soft_delete(user_id, session)
