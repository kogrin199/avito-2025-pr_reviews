from sqlalchemy.ext.asyncio import AsyncSession

from app.models.models import User
from app.repositories.user_repository import UserRepository


class UserService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.user_repo = UserRepository(db)

    async def get_user(self, user_id: str) -> User | None:
        return await self.user_repo.get_user(user_id)

    async def set_is_active(self, user_id: str, is_active: bool) -> User | None:
        return await self.user_repo.set_is_active(user_id, is_active)
