from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.models.models import PullRequest, PullRequestReviewer


class PRRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_pr(self, pr_id: str) -> PullRequest | None:
        result = await self.db.execute(
            select(PullRequest).where(PullRequest.pull_request_id == pr_id)
        )
        return result.scalar_one_or_none()

    async def add_pr(self, pr: PullRequest) -> PullRequest:
        self.db.add(pr)
        await self.db.commit()
        await self.db.refresh(pr)
        return pr

    async def add_reviewer(self, pr_id: str, reviewer_id: str):
        reviewer = PullRequestReviewer(
            id=f"{pr_id}_{reviewer_id}", pull_request_id=pr_id, reviewer_id=reviewer_id
        )
        self.db.add(reviewer)
        await self.db.commit()
