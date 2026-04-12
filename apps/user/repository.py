from sqlalchemy import select
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from settings.settings import settings
from apps.user.models import User, Base
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


class UserRepository:
    """

    Класс для взаимодействия с пользователем

    """

    @staticmethod
    async def get_by_email(session, email: str):
        return await session.scalar(select(User).where(User.email == email))

    @staticmethod
    async def get_by_id(session, user_id: int):
        return await session.get(User, user_id)

    @staticmethod
    async def create(session, user: User):
        session.add(user)
        await session.commit()
        await session.refresh(user)
        return user


async def init_db():
    """
    Автоматически создавать таблицы базы данных, если они не существуют
    """
    await ensure_database_exists()

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        print("Tables created/updated!")
