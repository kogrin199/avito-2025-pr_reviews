from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.schemas.schemas import UserResponse, user_to_schema
from app.services.user_service import UserService

router = APIRouter(prefix="/users", tags=["Users"])


class SetIsActiveRequest(BaseModel):
    user_id: str
    is_active: bool


@router.post("/setIsActive", response_model=UserResponse)
async def set_is_active(payload: SetIsActiveRequest, db: AsyncSession = Depends(get_db)):
    service = UserService(db)
    user = await service.set_is_active(payload.user_id, payload.is_active)
    if not user:
        raise HTTPException(
            status_code=404, detail={"error": {"code": "NOT_FOUND", "message": "User not found"}}
        )
    return {"user": user_to_schema(user)}
