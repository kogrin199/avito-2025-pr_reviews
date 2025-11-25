"""
Unit тесты для TeamService и UserService
"""

from unittest.mock import AsyncMock

import pytest

from app.models.models import Team, User
from app.services.team_service import TeamService
from app.services.user_service import UserService

# =============================================================================
# TEAM SERVICE
# =============================================================================


@pytest.fixture
def mock_db():
    """
    Mock AsyncSession
    """
    return AsyncMock()


@pytest.fixture
def team_service(mock_db):
    return TeamService(mock_db)


@pytest.fixture
def user_service(mock_db):
    return UserService(mock_db)


class TestTeamService:
    """
    Тесты TeamService
    """

    async def test_get_team_found(self, team_service: TeamService):
        """
        Команда найдена
        """
        team = Team(team_name="backend")
        team.members = [
            User(user_id="u1", username="User1", is_active=True, team_name="backend"),
        ]

        team_service.team_repo.get_team = AsyncMock(return_value=team)

        result = await team_service.get_team("backend")

        assert result is not None
        assert result.team_name == "backend"
        team_service.team_repo.get_team.assert_called_once_with("backend")

    async def test_get_team_not_found(self, team_service: TeamService):
        """
        Команда не найдена
        """
        team_service.team_repo.get_team = AsyncMock(return_value=None)

        result = await team_service.get_team("nonexistent")

        assert result is None

    async def test_add_team_success(self, team_service: TeamService):
        """
        Успешное создание команды
        """
        members_data = [
            {"user_id": "u1", "username": "User1", "is_active": True},
            {"user_id": "u2", "username": "User2", "is_active": False},
        ]
        created_team = Team(team_name="new_team")

        team_service.team_repo.add_team = AsyncMock(return_value=created_team)

        result = await team_service.add_team("new_team", members_data)

        assert result.team_name == "new_team"
        team_service.team_repo.add_team.assert_called_once_with("new_team", members_data)


# =============================================================================
# USER SERVICE
# =============================================================================


class TestUserService:
    """
    Тесты UserService
    """

    async def test_get_user_found(self, user_service: UserService):
        """
        Пользователь найден
        """
        user = User(user_id="u1", username="TestUser", is_active=True, team_name="team1")
        user_service.user_repo.get_user = AsyncMock(return_value=user)
        result = await user_service.get_user("u1")

        assert result is not None
        assert result.user_id == "u1"
        assert result.username == "TestUser"

    async def test_get_user_not_found(self, user_service: UserService):
        """
        Пользователь не найден
        """
        user_service.user_repo.get_user = AsyncMock(return_value=None)
        result = await user_service.get_user("unknown")

        assert result is None

    async def test_set_is_active_activate(self, user_service: UserService):
        """
        Активация пользователя
        """
        user = User(user_id="u1", username="TestUser", is_active=True, team_name="team1")
        user_service.user_repo.set_is_active = AsyncMock(return_value=user)
        result = await user_service.set_is_active("u1", True)

        assert result is not None
        assert result.is_active is True
        user_service.user_repo.set_is_active.assert_called_once_with("u1", True)

    async def test_set_is_active_deactivate(self, user_service: UserService):
        """
        Деактивация пользователя
        """
        user = User(user_id="u1", username="TestUser", is_active=False, team_name="team1")
        user_service.user_repo.set_is_active = AsyncMock(return_value=user)
        result = await user_service.set_is_active("u1", False)

        assert result is not None
        assert result.is_active is False

    async def test_set_is_active_user_not_found(self, user_service: UserService):
        """
        Пользователь не найден при изменении статуса
        """
        user_service.user_repo.set_is_active = AsyncMock(return_value=None)
        result = await user_service.set_is_active("unknown", True)

        assert result is None
