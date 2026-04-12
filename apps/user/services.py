from .models import User
from apps.auth.services import hash_password


class UserService:
    def __init__(self, repo):
        self.repo = repo

    async def register(self, email: str, password: str, role_id: int):
        if await self.repo.get_by_email(email):
            raise ValueError("User already exists")
        user = User(email=email, password_hash=hash_password(password), role_id=role_id)
        return await self.repo.create(user)

    async def soft_delete(self, user: User):
        user.is_active = False
        await self.repo.session.commit()
