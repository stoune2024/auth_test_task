from typing import Annotated, Any

from fastapi import Depends
from pydantic import EmailStr
from sqlalchemy import select
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from settings.settings import settings
from apps.user.schemas import Base, User, BlacklistedToken, AccessRule
from sqlalchemy import text

engine = create_async_engine(settings.db_url, echo=False, future=True)

SessionLocal = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)


async def ensure_database_exists():
    """
    Проверяет наличие БД authdb, если нет — создаёт её.
    Использует подключение к "postgres" (системной базе).
    """
    root_engine = create_async_engine(
        settings.system_db_url, isolation_level="AUTOCOMMIT"
    )
    async with root_engine.connect() as conn:
        # Проверяем, существует ли база
        result = await conn.execute(
            text("SELECT 1 FROM pg_database WHERE datname = 'authdb'")
        )
        exists = result.scalar() is not None
        if not exists:
            await conn.execute(
                text("CREATE DATABASE authdb OWNER postgres ENCODING 'UTF8';")
            )
            print("Database created")
        else:
            print("Database exists!")
    await root_engine.dispose()


async def get_session() -> AsyncSession:
    async with SessionLocal() as session:
        yield session


SessionDep = Annotated[Any, Depends(get_session)]


class UserRepository:
    """

    Класс для взаимодействия с БД

    """

    @staticmethod
    async def get_by_email(session, email: EmailStr):
        return await session.scalar(select(User).where(User.email == email))

    @staticmethod
    async def get_by_id(session, user_id: int):
        return await session.get(User, user_id)

    @staticmethod
    async def create(session, user: User):
        user_db = User(
            email=user.email,
            password_hash=user.password_hash,
            is_active=user.is_active,
            role_id=user.role_id,
        )
        session.add(user_db)
        await session.commit()
        await session.refresh(user_db)
        return user

    @staticmethod
    async def update_user(user_id, user, session):
        """
        Обновляет пользователя и сохраняет в БД. Решил не усложнять доп. проверками и ограничился только обновлением email
        """

        try:
            db_data = await session.get(User, user_id)

            db_data.email = user.email
            session.add(db_data)
            await session.commit()
            await session.refresh(db_data)
            return {"message": "User updated!"}
        except Exception as e:
            await session.rollback()
            return {"message": f"something went wrong...: {e}"}

    @staticmethod
    async def soft_delete(user_id, session):
        try:
            db_data = await session.get(User, user_id)

            db_data.is_active = False
            session.add(db_data)
            await session.commit()
            await session.refresh(db_data)
            return {"message": "User soft deleted!"}
        except Exception as e:
            await session.rollback()
            return {"message": f"something went wrong...: {e}"}

    @staticmethod
    async def blacklist_token(session, token: str):
        blacklisted = BlacklistedToken(token=token)

        session.add(blacklisted)

        await session.commit()

        return blacklisted

    @staticmethod
    async def is_token_blacklisted(session, token: str) -> bool:
        existing = await session.scalar(
            select(BlacklistedToken).where(BlacklistedToken.token == token)
        )

        return existing is not None

    @staticmethod
    async def get_rules(session):
        result = await session.execute(select(AccessRule))

        return result.scalars().all()


async def init_db():
    """
    Автоматически создавать таблицы базы данных, если они не существуют
    """
    await ensure_database_exists()

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        print("Tables created/updated!")
