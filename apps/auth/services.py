import bcrypt, jwt
from datetime import datetime, timedelta

from fastapi import HTTPException, status, Depends, Request

from settings.settings import settings, SettingsDep
from apps.user.repository import UserRepository, SessionDep
from datetime import timedelta

from typing_extensions import Annotated


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()


def verify_password(password: str, hashed: str) -> bool:
    return bcrypt.checkpw(password.encode(), hashed.encode())


def create_token(role_id: int, type: str):
    payload = {
        "role_id": role_id,
        "type": type,
        "exp": datetime.utcnow()
        + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES),
    }
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def decode_token(token: str):
    return jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])


async def authenticate_user(email: str, password: str, session: SessionDep):
    user = await UserRepository.get_by_email(session, email)
    if not verify_password(password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Введен неверный пароль",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user


async def generate_tokens(form_data, session: SessionDep):
    user = await authenticate_user(form_data.email, form_data.password, session)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Пользователь не найден",
        )

    access_token = create_token(user.role_id, type="access")
    # Далее в проекте refresh_token нигде не используется во избежание излишества. Однако функционал для дальнейшей работы с ним заложен здесь.
    refresh_token = create_token(user.role_id, type="refresh")
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
    }


def verify_token(request: Request):
    try:
        token = request.cookies.get("access-token")
        token_payload = jwt.decode(
            token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
        )
        role_id: int = token_payload.get("role_id")
        return role_id
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Пользователь не авторизован: {e}",
        )


ProtectionDep = Annotated[int, Depends(verify_token)]
