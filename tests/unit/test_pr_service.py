"""
Unit тесты для PullRequestService

Тестируем бизнес-логику с mock-ами репозиториев
"""

import datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.models.models import PRStatus, PullRequest, PullRequestReviewer, Team, User
from app.services.pr_service import PullRequestService
from app.services.pr_service_errors import (
    AuthorNotFoundError,
    NoCandidateError,
    PRExistsError,
    PRMergedError,
    PRNotFoundError,
    ReviewerNotAssignedError,
    TeamNotFoundError,
)


@pytest.fixture
def mock_db():
    """
    Mock AsyncSession
    """
    db = AsyncMock()
    db.commit = AsyncMock()
    db.delete = AsyncMock()
    return db


@pytest.fixture
def pr_service(mock_db):
    """
    PullRequestService с mock сессией
    """
    return PullRequestService(mock_db)


# =============================================================================
# CREATE PR
# =============================================================================


class TestCreatePR:
    """
    Тесты создания Pull Request
    """

    async def test_create_pr_success(self, pr_service: PullRequestService):
        """
        Успешное создание PR с назначением ревьюверов
        """
        # Arrange
        author = User(user_id="author1", username="Author", is_active=True, team_name="team1")
        member1 = User(user_id="m1", username="Member1", is_active=True, team_name="team1")
        member2 = User(user_id="m2", username="Member2", is_active=True, team_name="team1")
        team = MagicMock(spec=Team)
        team.members = [author, member1, member2]

        created_pr = PullRequest(
            pull_request_id="pr-1",
            pull_request_name="Test PR",
            author_id="author1",
            status=PRStatus.OPEN,
            createdAt=datetime.datetime.now(datetime.UTC),
        )
        created_pr.reviewers = [
            PullRequestReviewer(pull_request_id="pr-1", reviewer_id="m1"),
            PullRequestReviewer(pull_request_id="pr-1", reviewer_id="m2"),
        ]

        pr_service.pr_repo.get_pr = AsyncMock(return_value=None)
        pr_service.user_repo.get_user = AsyncMock(return_value=author)
        pr_service.team_repo.get_team = AsyncMock(return_value=team)
        pr_service.pr_repo.add_pr = AsyncMock(return_value=created_pr)
        pr_service.pr_repo.add_reviewer = AsyncMock()
        pr_service.pr_repo.get_pr_with_reviewers = AsyncMock(return_value=created_pr)

        # act
        result = await pr_service.create_pr("pr-1", "Test PR", "author1")

        # assert
        assert result.pull_request_id == "pr-1"
        assert result.status == PRStatus.OPEN

        pr_service.pr_repo.add_pr.assert_called_once()
        # должны быть назначены 2 ревьювера (не автор)
        assert pr_service.pr_repo.add_reviewer.call_count == 2

    async def test_create_pr_already_exists(self, pr_service: PullRequestService):
        """
        PR с таким ID уже существует
        """
        existing_pr = PullRequest(
            pull_request_id="pr-1",
            pull_request_name="Existing",
            author_id="author1",
            status=PRStatus.OPEN,
        )
        pr_service.pr_repo.get_pr = AsyncMock(return_value=existing_pr)

        with pytest.raises(PRExistsError):
            await pr_service.create_pr("pr-1", "New PR", "author1")

    async def test_create_pr_author_not_found(self, pr_service: PullRequestService):
        """
        Автор не найден в системе
        """
        pr_service.pr_repo.get_pr = AsyncMock(return_value=None)
        pr_service.user_repo.get_user = AsyncMock(return_value=None)

        with pytest.raises(AuthorNotFoundError):
            await pr_service.create_pr("pr-1", "Test PR", "unknown_author")

    async def test_create_pr_team_not_found(self, pr_service: PullRequestService):
        """
        Команда автора не найдена (edge case)
        """
        author = User(
            user_id="author1", username="Author", is_active=True, team_name="missing_team"
        )

        pr_service.pr_repo.get_pr = AsyncMock(return_value=None)
        pr_service.user_repo.get_user = AsyncMock(return_value=author)
        pr_service.team_repo.get_team = AsyncMock(return_value=None)

        with pytest.raises(TeamNotFoundError):
            await pr_service.create_pr("pr-1", "Test PR", "author1")

    async def test_create_pr_no_active_reviewers(self, pr_service: PullRequestService):
        """
        Команда без активных участников кроме автора — PR создаётся без ревьюверов
        """
        author = User(user_id="author1", username="Author", is_active=True, team_name="team1")
        inactive = User(user_id="m1", username="Inactive", is_active=False, team_name="team1")
        team = MagicMock(spec=Team)
        team.members = [author, inactive]

        created_pr = PullRequest(
            pull_request_id="pr-1",
            pull_request_name="Test PR",
            author_id="author1",
            status=PRStatus.OPEN,
        )
        created_pr.reviewers = []

        pr_service.pr_repo.get_pr = AsyncMock(return_value=None)
        pr_service.user_repo.get_user = AsyncMock(return_value=author)
        pr_service.team_repo.get_team = AsyncMock(return_value=team)
        pr_service.pr_repo.add_pr = AsyncMock(return_value=created_pr)
        pr_service.pr_repo.add_reviewer = AsyncMock()
        pr_service.pr_repo.get_pr_with_reviewers = AsyncMock(return_value=created_pr)

        result = await pr_service.create_pr("pr-1", "Test PR", "author1")

        assert result.pull_request_id == "pr-1"
        # add_reviewer не вызывался — нет кандидатов
        pr_service.pr_repo.add_reviewer.assert_not_called()

    async def test_create_pr_one_candidate(self, pr_service: PullRequestService):
        """
        Только один кандидат — назначается один ревьювер
        """
        author = User(user_id="author1", username="Author", is_active=True, team_name="team1")
        member = User(user_id="m1", username="Member", is_active=True, team_name="team1")
        team = MagicMock(spec=Team)
        team.members = [author, member]

        created_pr = PullRequest(
            pull_request_id="pr-1",
            pull_request_name="Test PR",
            author_id="author1",
            status=PRStatus.OPEN,
        )

        pr_service.pr_repo.get_pr = AsyncMock(return_value=None)
        pr_service.user_repo.get_user = AsyncMock(return_value=author)
        pr_service.team_repo.get_team = AsyncMock(return_value=team)
        pr_service.pr_repo.add_pr = AsyncMock(return_value=created_pr)
        pr_service.pr_repo.add_reviewer = AsyncMock()
        pr_service.pr_repo.get_pr_with_reviewers = AsyncMock(return_value=created_pr)

        await pr_service.create_pr("pr-1", "Test PR", "author1")

        # только 1 ревьювер назначен
        pr_service.pr_repo.add_reviewer.assert_called_once_with("pr-1", "m1")


# =============================================================================
# MERGE PR
# =============================================================================


class TestMergePR:
    """
    Тесты мерджа Pull Request
    """

    async def test_merge_pr_success(self, pr_service: PullRequestService):
        """
        Успешный мердж открытого PR
        """
        pr = PullRequest(
            pull_request_id="pr-1",
            pull_request_name="Test",
            author_id="author1",
            status=PRStatus.OPEN,
        )
        merged_pr = PullRequest(
            pull_request_id="pr-1",
            pull_request_name="Test",
            author_id="author1",
            status=PRStatus.MERGED,
            mergedAt=datetime.datetime.now(datetime.UTC),
        )

        pr_service.pr_repo.get_pr = AsyncMock(return_value=pr)
        pr_service.pr_repo.get_pr_with_reviewers = AsyncMock(return_value=merged_pr)

        result = await pr_service.merge_pr("pr-1")

        assert result.status == PRStatus.MERGED
        assert result.mergedAt is not None
        pr_service.db.commit.assert_called_once()

    async def test_merge_pr_not_found(self, pr_service: PullRequestService):
        """
        PR не найден
        """
        pr_service.pr_repo.get_pr = AsyncMock(return_value=None)

        with pytest.raises(PRNotFoundError):
            await pr_service.merge_pr("nonexistent")

    async def test_merge_pr_idempotent(self, pr_service: PullRequestService):
        """
        Повторный мердж уже смердженного PR — идемпотентность
        """
        merged_pr = PullRequest(
            pull_request_id="pr-1",
            pull_request_name="Test",
            author_id="author1",
            status=PRStatus.MERGED,
            mergedAt=datetime.datetime.now(datetime.UTC),
        )

        pr_service.pr_repo.get_pr = AsyncMock(return_value=merged_pr)
        pr_service.pr_repo.get_pr_with_reviewers = AsyncMock(return_value=merged_pr)

        result = await pr_service.merge_pr("pr-1")

        # не должно быть повторного commit
        pr_service.db.commit.assert_not_called()
        assert result.status == PRStatus.MERGED


# =============================================================================
# REASSIGN REVIEWER
# =============================================================================


class TestReassignReviewer:
    """
    Тесты переназначения ревьювера
    """

    async def test_reassign_success(self, pr_service: PullRequestService):
        """
        Успешное переназначение ревьювера
        """
        pr = PullRequest(
            pull_request_id="pr-1",
            pull_request_name="Test",
            author_id="author1",
            status=PRStatus.OPEN,
        )
        old_reviewer = User(user_id="old_rev", username="OldRev", is_active=True, team_name="team1")
        new_candidate = User(
            user_id="new_rev", username="NewRev", is_active=True, team_name="team1"
        )
        team = MagicMock(spec=Team)
        team.members = [old_reviewer, new_candidate]

        reviewer_obj = PullRequestReviewer(pull_request_id="pr-1", reviewer_id="old_rev")

        pr_service.pr_repo.get_pr = AsyncMock(return_value=pr)
        pr_service.reviewer_repo.get_reviewers_by_pr = AsyncMock(return_value=[reviewer_obj])
        pr_service.user_repo.get_user = AsyncMock(return_value=old_reviewer)
        pr_service.team_repo.get_team = AsyncMock(return_value=team)
        pr_service.pr_repo.add_reviewer = AsyncMock()
        pr_service.pr_repo.get_pr_with_reviewers = AsyncMock(return_value=pr)

        result_pr, new_reviewer_id = await pr_service.reassign_reviewer("pr-1", "old_rev")

        assert new_reviewer_id == "new_rev"
        pr_service.db.delete.assert_called_once_with(reviewer_obj)
        pr_service.pr_repo.add_reviewer.assert_called_once_with("pr-1", "new_rev")

    async def test_reassign_pr_not_found(self, pr_service: PullRequestService):
        """
        PR не найден при переназначении
        """
        pr_service.pr_repo.get_pr = AsyncMock(return_value=None)

        with pytest.raises(PRNotFoundError):
            await pr_service.reassign_reviewer("nonexistent", "reviewer1")

    async def test_reassign_pr_merged(self, pr_service: PullRequestService):
        """
        Нельзя переназначить в смердженном PR
        """
        merged_pr = PullRequest(
            pull_request_id="pr-1",
            pull_request_name="Test",
            author_id="author1",
            status=PRStatus.MERGED,
        )
        pr_service.pr_repo.get_pr = AsyncMock(return_value=merged_pr)

        with pytest.raises(PRMergedError):
            await pr_service.reassign_reviewer("pr-1", "reviewer1")

    async def test_reassign_reviewer_not_assigned(self, pr_service: PullRequestService):
        """
        Ревьювер не назначен на этот PR
        """
        pr = PullRequest(
            pull_request_id="pr-1",
            pull_request_name="Test",
            author_id="author1",
            status=PRStatus.OPEN,
        )
        other_reviewer = PullRequestReviewer(pull_request_id="pr-1", reviewer_id="other")

        pr_service.pr_repo.get_pr = AsyncMock(return_value=pr)
        pr_service.reviewer_repo.get_reviewers_by_pr = AsyncMock(return_value=[other_reviewer])

        with pytest.raises(ReviewerNotAssignedError):
            await pr_service.reassign_reviewer("pr-1", "not_assigned")

    async def test_reassign_no_candidates(self, pr_service: PullRequestService):
        """
        Нет кандидатов для замены
        """
        pr = PullRequest(
            pull_request_id="pr-1",
            pull_request_name="Test",
            author_id="author1",
            status=PRStatus.OPEN,
        )
        old_reviewer = User(user_id="old_rev", username="OldRev", is_active=True, team_name="team1")
        inactive = User(user_id="inactive", username="Inactive", is_active=False, team_name="team1")
        team = MagicMock(spec=Team)
        team.members = [old_reviewer, inactive]  # только неактивный остался

        reviewer_obj = PullRequestReviewer(pull_request_id="pr-1", reviewer_id="old_rev")

        pr_service.pr_repo.get_pr = AsyncMock(return_value=pr)
        pr_service.reviewer_repo.get_reviewers_by_pr = AsyncMock(return_value=[reviewer_obj])
        pr_service.user_repo.get_user = AsyncMock(return_value=old_reviewer)
        pr_service.team_repo.get_team = AsyncMock(return_value=team)

        with pytest.raises(NoCandidateError):
            await pr_service.reassign_reviewer("pr-1", "old_rev")


# =============================================================================
# GET PRS BY REVIEWER
# =============================================================================


class TestGetPRsByReviewer:
    """
    Тесты получения PR по ревьюверу
    """

    async def test_get_prs_by_reviewer_success(self, pr_service: PullRequestService):
        """
        Получение списка PR для ревьювера
        """
        pr1 = PullRequest(
            pull_request_id="pr-1", pull_request_name="PR1", author_id="a1", status=PRStatus.OPEN
        )
        pr2 = PullRequest(
            pull_request_id="pr-2", pull_request_name="PR2", author_id="a2", status=PRStatus.MERGED
        )

        reviewer_prs = [
            MagicMock(pull_request=pr1),
            MagicMock(pull_request=pr2),
        ]

        pr_service.reviewer_repo.get_prs_by_reviewer = AsyncMock(return_value=reviewer_prs)
        result = await pr_service.get_prs_by_reviewer("reviewer1")

        assert len(result) == 2
        assert result[0].pull_request_id == "pr-1"
        assert result[1].pull_request_id == "pr-2"

    async def test_get_prs_by_reviewer_empty(self, pr_service: PullRequestService):
        """
        Ревьювер не назначен ни на один PR
        """
        pr_service.reviewer_repo.get_prs_by_reviewer = AsyncMock(return_value=[])
        result = await pr_service.get_prs_by_reviewer("reviewer_without_prs")

        assert result == []
