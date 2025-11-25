from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.models.models import User


class UserRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_user(self, user_id: str) -> User | None:
        result = await self.db.execute(select(User).where(User.user_id == user_id))
        return result.scalar_one_or_none()

    async def set_is_active(self, user_id: str, is_active: bool) -> User | None:
        user = await self.get_user(user_id)
        if user:
            user.is_active = is_active
            await self.db.commit()
            await self.db.refresh(user)
        return user
