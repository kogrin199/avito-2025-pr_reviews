from sqlalchemy.ext.asyncio import AsyncSession

from app.models.models import Team
from app.repositories.team_repository import TeamRepository


class TeamService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.team_repo = TeamRepository(db)

    async def get_team(self, team_name: str) -> Team | None:
        return await self.team_repo.get_team(team_name)

    async def add_team(self, team_name: str, members: list[dict]) -> Team:
        return await self.team_repo.add_team(team_name, members)
