"""
Интеграционные тесты для /stats
"""

from httpx import AsyncClient
import pytest


class TestStats:
    """
    Тесты GET /stats
    """

    @pytest.mark.asyncio
    async def test_stats_empty(self, client: AsyncClient):
        """
        Статистика на пустой БД
        """
        response = await client.get("/stats")
        assert response.status_code == 200

        data = response.json()
        assert data["total_prs"] == 0
        assert data["total_reviews"] == 0
        assert "prs_by_status" in data
        assert "top_reviewers" in data
        assert data["top_reviewers"] == []

    @pytest.mark.asyncio
    async def test_stats_with_data(self, client: AsyncClient):
        """
        Статистика с данными
        """
        # Создаём команду с 3 участниками
        await client.post(
            "/team/add",
            json={
                "team_name": "stats-team",
                "members": [
                    {"user_id": "s1", "username": "Alice", "is_active": True},
                    {"user_id": "s2", "username": "Bob", "is_active": True},
                    {"user_id": "s3", "username": "Carol", "is_active": True},
                ],
            },
        )

        # Создаём 2 PR (s1 автор -> s2, s3 ревьюверы)
        await client.post(
            "/pullRequest/create",
            json={
                "pull_request_id": "pr-stats-1",
                "pull_request_name": "Stats PR 1",
                "author_id": "s1",
            },
        )
        await client.post(
            "/pullRequest/create",
            json={
                "pull_request_id": "pr-stats-2",
                "pull_request_name": "Stats PR 2",
                "author_id": "s1",
            },
        )

        # Мержим один PR
        await client.post(
            "/pullRequest/merge",
            json={"pull_request_id": "pr-stats-1"},
        )

        # Проверяем статистику
        response = await client.get("/stats")
        assert response.status_code == 200

        data = response.json()
        assert data["total_prs"] == 2
        assert data["total_reviews"] == 4  # 2 PR * 2 ревьювера

        # Проверяем статусы
        statuses = {s["status"]: s["count"] for s in data["prs_by_status"]}
        assert statuses.get("OPEN", 0) == 1
        assert statuses.get("MERGED", 0) == 1

        # Проверяем топ ревьюверов
        assert len(data["top_reviewers"]) == 2
        # s2 и s3 должны быть ревьюверами, каждый по 2 раза
        reviewer_counts = {r["user_id"]: r["review_count"] for r in data["top_reviewers"]}
        assert "s2" in reviewer_counts
        assert "s3" in reviewer_counts
        assert reviewer_counts["s2"] == 2
        assert reviewer_counts["s3"] == 2

    @pytest.mark.asyncio
    async def test_stats_limit_parameter(self, client: AsyncClient):
        """
        Проверка параметра limit для топ ревьюверов
        """
        # Создаём команду
        await client.post(
            "/team/add",
            json={
                "team_name": "limit-team",
                "members": [
                    {"user_id": "l1", "username": "L1", "is_active": True},
                    {"user_id": "l2", "username": "L2", "is_active": True},
                    {"user_id": "l3", "username": "L3", "is_active": True},
                ],
            },
        )

        # Создаём PR
        await client.post(
            "/pullRequest/create",
            json={
                "pull_request_id": "pr-limit",
                "pull_request_name": "Limit PR",
                "author_id": "l1",
            },
        )

        # Запрос с limit=1
        response = await client.get("/stats?limit=1")
        assert response.status_code == 200

        data = response.json()
        assert len(data["top_reviewers"]) <= 1
