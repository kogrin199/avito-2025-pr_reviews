"""
Unit тесты для репозиториев

Тестируем SQL-операции с mock сессиями
"""

from unittest.mock import AsyncMock, MagicMock

import pytest

from app.models.models import Team, User
from app.repositories.team_repository import TeamRepository
from app.repositories.user_repository import UserRepository


@pytest.fixture
def mock_db() -> AsyncMock:
    """
    Mock AsyncSession
    """
    db = AsyncMock()
    db.execute = AsyncMock()
    db.add = MagicMock()
    db.flush = AsyncMock()
    db.commit = AsyncMock()
    db.refresh = AsyncMock()
    return db


class TestTeamRepository:
    """
    Тесты TeamRepository
    """

    async def test_get_team_found(self, mock_db):
        """
        Команда найдена
        """
        repo = TeamRepository(mock_db)
        team = Team(team_name="backend")

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = team
        mock_db.execute.return_value = mock_result

        result = await repo.get_team("backend")

        assert result == team
        mock_db.execute.assert_called_once()

    async def test_get_team_not_found(self, mock_db):
        """
        Команда не найдена
        """
        repo = TeamRepository(mock_db)

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute.return_value = mock_result

        result = await repo.get_team("nonexistent")

        assert result is None

    async def test_add_team_success(self, mock_db):
        """
        Успешное добавление команды
        """
        repo = TeamRepository(mock_db)

        team = Team(team_name="new_team")
        mock_result = MagicMock()
        mock_result.scalar_one.return_value = team
        mock_db.execute.return_value = mock_result

        members = [
            {"user_id": "u1", "username": "User1", "is_active": True},
            {"user_id": "u2", "username": "User2", "is_active": False},
        ]

        result = await repo.add_team("new_team", members)

        assert result == team
        # add вызван 3 раза: 1 team + 2 users
        assert mock_db.add.call_count == 3
        mock_db.flush.assert_called_once()
        mock_db.commit.assert_called_once()


class TestUserRepository:
    """
    Тесты UserRepository
    """

    async def test_get_user_found(self, mock_db):
        """
        Пользователь найден
        """
        repo = UserRepository(mock_db)
        user = User(user_id="u1", username="Test", is_active=True, team_name="team1")

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = user
        mock_db.execute.return_value = mock_result

        result = await repo.get_user("u1")

        assert result == user

    async def test_get_user_not_found(self, mock_db):
        """
        Пользователь не найден
        """
        repo = UserRepository(mock_db)

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute.return_value = mock_result

        result = await repo.get_user("nonexistent")

        assert result is None

    async def test_set_is_active_success(self, mock_db):
        """
        Успешное изменение статуса
        """
        repo = UserRepository(mock_db)
        user = User(user_id="u1", username="Test", is_active=True, team_name="team1")

        # Mock get_user внутри set_is_active
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = user
        mock_db.execute.return_value = mock_result

        result = await repo.set_is_active("u1", False)

        assert result == user
        assert user.is_active is False
        mock_db.commit.assert_called_once()
        mock_db.refresh.assert_called_once_with(user)

    async def test_set_is_active_user_not_found(self, mock_db):
        """
        Пользователь не найден при изменении статуса
        """
        repo = UserRepository(mock_db)

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute.return_value = mock_result

        result = await repo.set_is_active("nonexistent", True)

        assert result is None
        mock_db.commit.assert_not_called()
