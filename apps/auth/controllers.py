from typing import Annotated

from fastapi import Form, status, HTTPException, Request
from fastapi.responses import RedirectResponse
from apps.user.repository import UserRepository, SessionDep
from apps.auth.routers import auth_router
from apps.user.models import UserCreate, User, UserAuth
from apps.auth.services import hash_password, generate_tokens


@auth_router.post("/reg")
async def register_user(
    user: Annotated[UserCreate, Form()],
    session: SessionDep,
):
    """
    Эндпоинт создания (регистрации нового пользователя)
    :param user: Данные о пользователе, приходящие из HTML формы. Валидируются Pydantic моделью UserCreate
    :param session: Объект типа Session (сессия) для взаимодействия с БД
    :return: JSON-объект, сообщающий о результате выполнения эндпоинта и возвращающий пользователя в виде словаря
    """
    try:
        user_dict = user.model_dump()
        hashed_password = hash_password(user.password)
        extra_data = {"password_hash": hashed_password}
        user_dict.update(extra_data)
        user_model = User.model_validate(user_dict)
        user = await UserRepository.create(session, user_model)
        return {"message": f"user is created, his id is: {user.id}"}
    except (AttributeError, Exception) as e:
        return {"message": f"something_went_wrong...{e}"}


@auth_router.post("/login/")
async def validate_login_form(
    form_data: Annotated[UserAuth, Form()],
    session: SessionDep,
):
    """
    Эндпоинт аутентификации/авторизации зарегистрированного пользователя
    """
    user = await UserRepository.get_by_email(session, form_data.email)
    if user.is_active:
        tokens = await generate_tokens(form_data, session)
        access_token = tokens.get("access_token")

        response = RedirectResponse(
            "/auth/suc_auth", status_code=status.HTTP_303_SEE_OTHER
        )
        response.set_cookie(
            key="access-token", value=access_token, httponly=True, secure=True
        )

        return response
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Учетная запись удалена (неактивна)",
    )


@auth_router.get("/log_out")
async def log_out(session: SessionDep, request: Request):

    token = request.cookies.get("access-token")

    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Токен доступа не найден",
        )

    await UserRepository.blacklist_token(session, token)

    response = RedirectResponse(
        "/auth/suc_log_out", status_code=status.HTTP_303_SEE_OTHER
    )

    response.delete_cookie(key="access-token")

    return response


@auth_router.get("/suc_auth")
def successfull_auth():
    """
    Эндпоинт для редиректа после успешной авторизации
    :return: JSON-оповещение
    """
    return {"message": "Авторизация успешна, токен доступа сохранен в куках!"}


@auth_router.get("/suc_log_out")
def successfull_log_out():
    """
    Эндпоинт для редиректа после успешной авторизации
    :return: JSON-оповещение
    """
    return {"message": "Вы успешно вышли из учетной записи!"}
