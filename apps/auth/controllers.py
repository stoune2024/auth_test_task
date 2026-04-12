from typing import Annotated, Any

from fastapi import Form, status, Body
from fastapi.responses import RedirectResponse
from apps.user.repository import UserRepository, SessionDep
from apps.auth.routers import auth_router
from apps.user.models import UserCreate, User, UserPublic, UserAuth
from apps.auth.services import hash_password, generate_tokens
from settings.settings import SettingsDep


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
    tokens = await generate_tokens(form_data, session)
    access_token = tokens.get("access_token")
    refresh_token = tokens.get("refresh_token")

    redirect_url = "/auth/suc_auth"
    headers = {"Authorization": f"Bearer {access_token}"}
    response = RedirectResponse(
        redirect_url, status_code=status.HTTP_303_SEE_OTHER, headers=headers
    )
    response.set_cookie(
        key="access-token", value=access_token, httponly=True, secure=True
    )
    response.set_cookie(
        key="refresh-token", value=refresh_token, httponly=True, secure=True
    )
    return response


@auth_router.get("/suc_auth")
def successfull_auth():
    """
    Эндпоинт для редиректа после успешной авторизации
    :return: JSON-оповещение
    """
    return {"message": "Авторизация успешна, токен доступа сохранен в куках!"}


# @auth_router.patch("/users/{user_id}", response_model=UserPublic)
# def update_user(
#     user_id: Annotated[int, Path(title="Идентификатор пользователя", ge=0, le=1000)],
#     user: Annotated[UserCreate, Form()],
#     connection: ConnectionDep,
#     protection: ProtectionDep,
# ):
#     """
#     Эндпоинт обновления данных о пользователе.
#     :param protection: Объект типа TokenData. Нужен для проверки авторизации пользователя
#     :param user_id: Параметр пути, обозначающий идентификатор искомого пользователя.
#     :param user: Данные о пользователе, приходящие из HTML формы. Валидируются Pydantic моделью UserUpdate
#     :param connection: Объект типа Connection (соединение) для взаимодействия с БД
#     :return: Объект пользователь, валидируемый моделью UserPublic
#     """
#     try:
#         if protection:
#             user_from_db = connection.read_user_by_id(user_id)
#             if not user_from_db:
#                 raise HTTPException(status_code=404, detail="Пользователь не найден")
#             user_data = user.model_dump(exclude_unset=True)
#             extra_data = {}
#             if "password" in user_data:
#                 password = user_data["password"]
#                 hashed_password = pwd_context.hash(password)
#                 extra_data["hashed_password"] = hashed_password
#             del user_data["password"]
#             user_from_db.update(user_data)
#             user_from_db.update(extra_data)
#             return user_from_db
#     except Exception as e:
#         return {"message": f"Возникла ошибка: {e}"}
