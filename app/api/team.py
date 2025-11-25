from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.schemas.schemas import Team, TeamResponse, team_to_schema
from app.services.team_service import TeamService

router = APIRouter(prefix="/team", tags=["Teams"])


@router.post("/add", response_model=TeamResponse, status_code=201)
async def add_team(team: Team, db: AsyncSession = Depends(get_db)):
    service = TeamService(db)
    try:
        result = await service.add_team(team.team_name, [m.model_dump() for m in team.members])
        return {"team": team_to_schema(result)}
    except Exception as e:
        raise HTTPException(
            status_code=400, detail={"error": {"code": "TEAM_EXISTS", "message": str(e)}}
        ) from e


@router.get("/get", response_model=Team)
async def get_team(
    team_name: str = Query(..., description="Уникальное имя команды"),
    db: AsyncSession = Depends(get_db),
):
    service = TeamService(db)
    team = await service.get_team(team_name)
    if not team:
        raise HTTPException(
            status_code=404, detail={"error": {"code": "NOT_FOUND", "message": "Team not found"}}
        )
    return team_to_schema(team)
