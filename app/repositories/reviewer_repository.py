from collections.abc import Sequence

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload

from app.models.models import PullRequestReviewer


class ReviewerRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_reviewers_by_pr(self, pr_id: str) -> Sequence[PullRequestReviewer]:
        result = await self.db.execute(
            select(PullRequestReviewer).where(PullRequestReviewer.pull_request_id == pr_id)
        )
        return result.scalars().all()

    async def get_prs_by_reviewer(self, reviewer_id: str) -> Sequence[PullRequestReviewer]:
        """
        Get all PR for a reviewer with eager loading of pull_request
        """
        result = await self.db.execute(
            select(PullRequestReviewer)
            .options(selectinload(PullRequestReviewer.pull_request))
            .where(PullRequestReviewer.reviewer_id == reviewer_id)
        )
        return result.scalars().all()
