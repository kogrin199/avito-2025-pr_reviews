from unittest.mock import AsyncMock

import pytest

from app.models.models import PRStatus, PullRequest, Team, User
from app.services.pr_service import PullRequestService


@pytest.mark.asyncio
async def test_assign_reviewers():
    db = AsyncMock()
    service = PullRequestService(db)
    # Мокаем репозитории
    service.user_repo.get_user = AsyncMock(
        return_value=User(user_id="u1", username="Alice", is_active=True, team_name="backend")
    )
    service.team_repo.get_team = AsyncMock(
        return_value=Team(
            team_name="backend",
            members=[
                User(user_id="u1", username="Alice", is_active=True, team_name="backend"),
                User(user_id="u2", username="Bob", is_active=True, team_name="backend"),
                User(user_id="u3", username="Eve", is_active=False, team_name="backend"),
            ],
        )
    )
    pr_obj = PullRequest(
        pull_request_id="pr-1",
        pull_request_name="Test",
        author_id="u1",
        status=PRStatus.OPEN,
    )
    pr_obj.assigned_reviewers = []
    service.pr_repo.add_pr = AsyncMock(return_value=pr_obj)
    service.pr_repo.add_reviewer = AsyncMock()
    pr = await service.create_pr("pr-1", "Test", "u1")
    assert pr.pull_request_id == "pr-1"
    # Проверяем, что назначены только активные и не автор
    service.pr_repo.add_reviewer.assert_called_with("pr-1", "u2")
