from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.schemas.schemas import User
from app.services.user_service import UserService

router = APIRouter(prefix="/users", tags=["Users"])


@router.post("/setIsActive", response_model=User)
async def set_is_active(payload: dict, db: AsyncSession = Depends(get_db)):
    user_id = payload.get("user_id")
    is_active = payload.get("is_active")
    service = UserService(db)
    user = await service.set_is_active(user_id, is_active)
    if not user:
        raise HTTPException(
            status_code=404, detail={"error": {"code": "NOT_FOUND", "message": "User not found"}}
        )
    return {"user": user}
