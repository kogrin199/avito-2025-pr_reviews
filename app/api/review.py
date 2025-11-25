from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.models.models import PullRequest as PullRequestModel
from app.schemas.schemas import PullRequestShort
from app.services.pr_service import PullRequestService

router = APIRouter(prefix="/users", tags=["Users"])


@router.get("/getReview", response_model=dict)
async def get_review(
    user_id: str = Query(..., description="Идентификатор пользователя"),
    db: AsyncSession = Depends(get_db),
):
    service = PullRequestService(db)
    prs: list[PullRequestModel] = await service.get_prs_by_reviewer(user_id)
    if prs is None:
        raise HTTPException(
            status_code=404, detail={"error": {"code": "NOT_FOUND", "message": "User not found"}}
        )
    return {
        "user_id": user_id,
        "pull_requests": [
            PullRequestShort(
                **{
                    "pull_request_id": pr.pull_request_id,
                    "pull_request_name": pr.pull_request_name,
                    "author_id": pr.author_id,
                    "status": pr.status.value if hasattr(pr.status, "value") else pr.status,
                }
            )
            for pr in prs
        ],
    }
