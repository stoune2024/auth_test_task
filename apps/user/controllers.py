from apps.user.routers import user_router
from fastapi import HTTPException, Path, Form, status
from typing_extensions import Annotated
from apps.user.repository import SessionDep
from utils.db_filler import seed_access_data
from apps.auth.services import ProtectionDep
from apps.user.models import UpdateUserSchema
from apps.user.repository import UserRepository


@user_router.post("/fill_db")
async def db_filler(session: SessionDep):
    await seed_access_data(session)


@user_router.get("/access-rules")
async def get_rules(protection: ProtectionDep, session: SessionDep):
    """
    Логику изменения правил доступа решил не писать, так как все упирается в банальный CRUD с проверкой ProtectionDep
    """
    if protection != 1:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Отсутствуют необходимые права",
        )
    return await UserRepository.get_rules(session)


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
            detail="Отсутствуют необходимые права",
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
            detail="Отсутствуют необходимые права",
        )
    return await UserRepository.soft_delete(user_id, session)
