from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.schemas.schemas import PullRequestReassignResponse, PullRequestResponse, pr_to_schema
from app.services.pr_service import (
    AuthorNotFoundError,
    NoCandidateError,
    PRExistsError,
    PRMergedError,
    PRNotFoundError,
    PullRequestService,
    ReviewerNotAssignedError,
    TeamNotFoundError,
)

router = APIRouter(prefix="/pullRequest", tags=["PullRequests"])


class CreatePRRequest(BaseModel):
    pull_request_id: str
    pull_request_name: str
    author_id: str


class MergePRRequest(BaseModel):
    pull_request_id: str


class ReassignRequest(BaseModel):
    pull_request_id: str
    old_user_id: str


@router.post("/create", response_model=PullRequestResponse, status_code=201)
async def create_pr(payload: CreatePRRequest, db: AsyncSession = Depends(get_db)):
    service = PullRequestService(db)
    try:
        pr = await service.create_pr(
            payload.pull_request_id, payload.pull_request_name, payload.author_id
        )
        return {"pr": pr_to_schema(pr)}

    except PRExistsError as e:
        raise HTTPException(
            status_code=409, detail={"error": {"code": "PR_EXISTS", "message": str(e)}}
        ) from e

    except (AuthorNotFoundError, TeamNotFoundError) as e:
        raise HTTPException(
            status_code=404, detail={"error": {"code": "NOT_FOUND", "message": str(e)}}
        ) from e


@router.post("/merge", response_model=PullRequestResponse)
async def merge_pr(payload: MergePRRequest, db: AsyncSession = Depends(get_db)):
    service = PullRequestService(db)
    try:
        pr = await service.merge_pr(payload.pull_request_id)
        return {"pr": pr_to_schema(pr)}

    except PRNotFoundError as e:
        raise HTTPException(
            status_code=404, detail={"error": {"code": "NOT_FOUND", "message": str(e)}}
        ) from e


@router.post("/reassign", response_model=PullRequestReassignResponse)
async def reassign_reviewer(payload: ReassignRequest, db: AsyncSession = Depends(get_db)):
    service = PullRequestService(db)
    try:
        pr, replaced_by = await service.reassign_reviewer(
            payload.pull_request_id, payload.old_user_id
        )
        return {"pr": pr_to_schema(pr), "replaced_by": replaced_by}

    except PRNotFoundError as e:
        raise HTTPException(
            status_code=404, detail={"error": {"code": "NOT_FOUND", "message": str(e)}}
        ) from e

    except PRMergedError as e:
        raise HTTPException(
            status_code=409, detail={"error": {"code": "PR_MERGED", "message": str(e)}}
        ) from e

    except ReviewerNotAssignedError as e:
        raise HTTPException(
            status_code=409, detail={"error": {"code": "NOT_ASSIGNED", "message": str(e)}}
        ) from e

    except NoCandidateError as e:
        raise HTTPException(
            status_code=409, detail={"error": {"code": "NO_CANDIDATE", "message": str(e)}}
        ) from e
