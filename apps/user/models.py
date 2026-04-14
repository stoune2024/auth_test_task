import re
from typing import Any, Optional

from pydantic import (
    BaseModel,
    Field,
    EmailStr,
    field_validator,
    ConfigDict,
)
from pydantic.alias_generators import to_camel

unique_user_ids_list = []


class UserPublic(BaseModel):
    id: int = Field(
        title="Уникальный идентификатор пользователя",
        description="Позволяет упорядочить пользователей",
    )
    email: EmailStr = Field(title="Электронная почта", description="Электронная почта")
    is_active: bool = Field(
        title="Является ли активным пользователем",
        description="Проверка на авторизацию",
    )
    role_id: int


class User(UserPublic):
    password_hash: str = Field(
        title="Хеш пользовательского пароля",
        description="Нужен для Oauth. Хранится в БД",
    )


class UserCreate(UserPublic):
    email: EmailStr
    password: str = Field(
        title="Пароль пользователя",
        description="Используется Oauth",
    )


class UserAuth(BaseModel):
    email: EmailStr
    password: str = Field(
        title="Пароль пользователя",
        description="Используется Oauth",
    )


class UpdateUserSchema(BaseModel):
    email: EmailStr | None = None
    password: str | None = None
