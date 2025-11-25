"""
Statistics endpoint - дополнительное задание
"""

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.models.models import PRStatus, PullRequest, PullRequestReviewer

router = APIRouter(prefix="/stats", tags=["Statistics"])


class UserReviewStats(BaseModel):
    user_id: str
    review_count: int


class PRStatusStats(BaseModel):
    status: str
    count: int


class StatsResponse(BaseModel):
    total_prs: int
    total_reviews: int
    prs_by_status: list[PRStatusStats]
    top_reviewers: list[UserReviewStats]


@router.get("", response_model=StatsResponse)
async def get_stats(
    db: AsyncSession = Depends(get_db),
    limit: int = 10,
):
    """
    Получить статистику по PR и назначениям ревьюверов.

    - total_prs: общее количество PR
    - total_reviews: общее количество назначений на ревью
    - prs_by_status: распределение PR по статусам (OPEN/MERGED)
    - top_reviewers: топ ревьюверов по количеству назначений
    """
    # Общее количество PR
    total_prs_result = await db.execute(select(func.count(PullRequest.pull_request_id)))
    total_prs = total_prs_result.scalar() or 0

    # Общее количество назначений
    total_reviews_result = await db.execute(select(func.count(PullRequestReviewer.id)))
    total_reviews = total_reviews_result.scalar() or 0

    # PR по статусам
    status_query = select(
        PullRequest.status, func.count(PullRequest.pull_request_id).label("count")
    ).group_by(PullRequest.status)
    status_result = await db.execute(status_query)
    prs_by_status = [
        PRStatusStats(
            status=row.status.value if hasattr(row.status, "value") else row.status,
            count=row.count,
        )
        for row in status_result.all()
    ]

    # Добавим отсутствующие статусы с count=0
    existing_statuses = {s.status for s in prs_by_status}
    for status in PRStatus:
        if status.value not in existing_statuses:
            prs_by_status.append(PRStatusStats(status=status.value, count=0))

    # Топ ревьюверов
    top_query = (
        select(
            PullRequestReviewer.reviewer_id,
            func.count(PullRequestReviewer.id).label("review_count"),
        )
        .group_by(PullRequestReviewer.reviewer_id)
        .order_by(func.count(PullRequestReviewer.id).desc())
        .limit(limit)
    )
    top_result = await db.execute(top_query)
    top_reviewers = [
        UserReviewStats(user_id=row.reviewer_id, review_count=row.review_count)
        for row in top_result.all()
    ]

    return StatsResponse(
        total_prs=total_prs,
        total_reviews=total_reviews,
        prs_by_status=prs_by_status,
        top_reviewers=top_reviewers,
    )
