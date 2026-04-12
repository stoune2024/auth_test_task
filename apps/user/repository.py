from sqlalchemy import select
from .models import User


class UserRepository:
    def __init__(self, session):
        self.session = session

    async def get_by_email(self, email: str):
        return await self.session.scalar(select(User).where(User.email == email))

    async def get_by_id(self, user_id: int):
        return await self.session.get(User, user_id)

    async def create(self, user: User):
        self.session.add(user)
        await self.session.commit()
        await self.session.refresh(user)
        return user
