from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.models.models import Team, User


class TeamRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_team(self, team_name: str) -> Team | None:
        result = await self.db.execute(select(Team).where(Team.team_name == team_name))
        return result.scalar_one_or_none()

    async def add_team(self, team_name: str, members: list[dict]) -> Team:
        team = Team(team_name=team_name)
        self.db.add(team)
        await self.db.flush()
        for member in members:
            user = User(
                user_id=member["user_id"],
                username=member["username"],
                is_active=member["is_active"],
                team_name=team_name,
            )
            self.db.add(user)
        await self.db.commit()
        await self.db.refresh(team)
        return team
