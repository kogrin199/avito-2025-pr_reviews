from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.schemas.schemas import PullRequest
from app.services.pr_service import PullRequestService

router = APIRouter(prefix="/pullRequest", tags=["PullRequests"])


@router.post("/create", response_model=PullRequest, status_code=201)
async def create_pr(payload: dict, db: AsyncSession = Depends(get_db)):
    pr_id = payload.get("pull_request_id")
    pr_name = payload.get("pull_request_name")
    author_id = payload.get("author_id")
    service = PullRequestService(db)
    try:
        pr = await service.create_pr(pr_id, pr_name, author_id)
        return {"pr": pr}
    except Exception as e:
        raise HTTPException(
            status_code=400, detail={"error": {"code": "PR_EXISTS", "message": str(e)}}
        ) from e


@router.post("/merge", response_model=PullRequest)
async def merge_pr(payload: dict, db: AsyncSession = Depends(get_db)):
    pr_id = payload.get("pull_request_id")
    service = PullRequestService(db)
    try:
        pr = await service.merge_pr(pr_id)
        return {"pr": pr}
    except Exception as e:
        raise HTTPException(
            status_code=404, detail={"error": {"code": "NOT_FOUND", "message": str(e)}}
        ) from e


@router.post("/reassign", response_model=PullRequest)
async def reassign_reviewer(payload: dict, db: AsyncSession = Depends(get_db)):
    pr_id = payload.get("pull_request_id")
    old_user_id = payload.get("old_user_id")
    service = PullRequestService(db)
    try:
        pr, replaced_by = await service.reassign_reviewer(pr_id, old_user_id)
        return {"pr": pr, "replaced_by": replaced_by}
    except Exception as e:
        raise HTTPException(
            status_code=409, detail={"error": {"code": "PR_MERGED", "message": str(e)}}
        ) from e
