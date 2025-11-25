from collections.abc import Sequence
import datetime
import random

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.models import PRStatus, PullRequest, PullRequestReviewer
from app.repositories.pr_repository import PRRepository
from app.repositories.reviewer_repository import ReviewerRepository
from app.repositories.team_repository import TeamRepository
from app.repositories.user_repository import UserRepository
from app.services.pr_service_errors import (
    AuthorNotFoundError,
    NoCandidateError,
    PRExistsError,
    PRMergedError,
    PRNotFoundError,
    ReviewerNotAssignedError,
    TeamNotFoundError,
)


class PullRequestService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.pr_repo = PRRepository(db)
        self.team_repo = TeamRepository(db)
        self.user_repo = UserRepository(db)
        self.reviewer_repo = ReviewerRepository(db)

    async def create_pr(self, pr_id: str, pr_name: str, author_id: str) -> PullRequest:
        # проверить, не существует ли уже PR
        existing_pr = await self.pr_repo.get_pr(pr_id)
        if existing_pr:
            raise PRExistsError("PR id already exists")

        author = await self.user_repo.get_user(author_id)
        if not author:
            raise AuthorNotFoundError("Author not found")

        team = await self.team_repo.get_team(author.team_name)
        if not team:
            raise TeamNotFoundError("Team not found")

        # выбрать до 2 активных ревьюверов из команды, кроме автора
        candidates = [m for m in team.members if m.is_active and m.user_id != author_id]
        reviewers = random.sample(candidates, min(2, len(candidates))) if candidates else []
        pr = PullRequest(
            pull_request_id=pr_id,
            pull_request_name=pr_name,
            author_id=author_id,
            status=PRStatus.OPEN,
            createdAt=datetime.datetime.now(datetime.UTC),
        )
        pr = await self.pr_repo.add_pr(pr)
        for reviewer in reviewers:
            await self.pr_repo.add_reviewer(pr_id, reviewer.user_id)

        # вернуть PR с загруженными ревьюверами
        return await self.pr_repo.get_pr_with_reviewers(pr_id)

    async def merge_pr(self, pr_id: str) -> PullRequest:
        pr = await self.pr_repo.get_pr(pr_id)

        if not pr:
            raise PRNotFoundError("PR not found")

        if pr.status == PRStatus.MERGED:
            # идемпотентность — вернуть PR с ревьюверами
            _res = await self.pr_repo.get_pr_with_reviewers(pr_id)
            return _res

        pr.status = PRStatus.MERGED
        pr.mergedAt = datetime.datetime.now(datetime.UTC)
        await self.db.commit()
        # вернуть PR с загруженными ревьюверами
        _res = await self.pr_repo.get_pr_with_reviewers(pr_id)
        return _res

    async def reassign_reviewer(self, pr_id: str, old_user_id: str) -> tuple[PullRequest, str]:
        pr = await self.pr_repo.get_pr(pr_id)
        if not pr:
            raise PRNotFoundError("PR not found")

        if pr.status == PRStatus.MERGED:
            raise PRMergedError("Cannot reassign on merged PR")
        reviewers = await self.reviewer_repo.get_reviewers_by_pr(pr_id)

        if old_user_id not in [r.reviewer_id for r in reviewers]:
            raise ReviewerNotAssignedError("Reviewer is not assigned to this PR")
        old_user = await self.user_repo.get_user(old_user_id)

        if not old_user:
            raise PRNotFoundError("Reviewer user not found")

        team = await self.team_repo.get_team(old_user.team_name)
        # исключить старого ревьювера и уже назначенных ревьюверов
        current_reviewer_ids = {r.reviewer_id for r in reviewers}
        candidates = [
            m
            for m in team.members
            if m.is_active and m.user_id != old_user_id and m.user_id not in current_reviewer_ids
        ]

        if not candidates:
            raise NoCandidateError("No active replacement candidate in team")
        new_reviewer = random.choice(candidates)

        # удалить старого ревьювера, добавить нового
        reviewer_obj = [r for r in reviewers if r.reviewer_id == old_user_id][0]
        await self.db.delete(reviewer_obj)
        await self.db.commit()
        await self.pr_repo.add_reviewer(pr_id, new_reviewer.user_id)

        # вернуть PR с загруженными ревьюверами
        _pr: PullRequest = await self.pr_repo.get_pr_with_reviewers(pr_id)
        return _pr, new_reviewer.user_id

    async def get_prs_by_reviewer(self, user_id: str) -> list[PullRequest]:
        reviewer_prs: Sequence[PullRequestReviewer] = await self.reviewer_repo.get_prs_by_reviewer(
            user_id
        )
        return [r.pull_request for r in reviewer_prs]
