"""
Интеграционные тесты для API пользователей (/users/*)

Тестируемые эндпоинты по OpenAPI:
- POST /users/setIsActive — установить флаг активности
- GET /users/getReview — получить PR'ы где пользователь ревьювер
"""

from httpx import AsyncClient


class TestUserSetIsActive:
    """
    Тесты POST /users/setIsActive
    """

    async def test_set_is_active_false(self, client: AsyncClient, sample_team_data: dict):
        """
        Деактивация пользователя — 200
        """
        # создаём команду с пользователями
        await client.post("/team/add", json=sample_team_data)

        # деактивируем пользователя
        response = await client.post(
            "/users/setIsActive",
            json={"user_id": "u1", "is_active": False},
        )

        assert response.status_code == 200
        data = response.json()

        assert "user" in data
        user = data["user"]
        assert user["user_id"] == "u1"
        assert user["is_active"] is False
        assert user["team_name"] == sample_team_data["team_name"]

    async def test_set_is_active_true(self, client: AsyncClient, sample_team_with_inactive: dict):
        """
        Активация неактивного пользователя — 200
        """
        # создаём команду с неактивным участником
        await client.post("/team/add", json=sample_team_with_inactive)

        # активируем его
        response = await client.post(
            "/users/setIsActive",
            json={"user_id": "f2", "is_active": True},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["user"]["is_active"] is True

    async def test_set_is_active_user_not_found(self, client: AsyncClient):
        """
        Установка активности несуществующему пользователю — 404
        """
        response = await client.post(
            "/users/setIsActive",
            json={"user_id": "nonexistent", "is_active": True},
        )

        assert response.status_code == 404
        data = response.json()
        assert data["detail"]["error"]["code"] == "NOT_FOUND"


class TestUserGetReview:
    """
    Тесты GET /users/getReview
    """

    async def test_get_review_empty_list(self, client: AsyncClient, sample_team_data: dict):
        """
        Пользователь без назначенных PR — пустой список, 200
        """
        # создаём команду
        await client.post("/team/add", json=sample_team_data)

        # запрашиваем PR'ы (их ещё нет)
        response = await client.get("/users/getReview", params={"user_id": "u1"})

        assert response.status_code == 200
        data = response.json()

        assert data["user_id"] == "u1"
        assert data["pull_requests"] == []

    async def test_get_review_with_prs(self, client: AsyncClient, sample_team_data: dict):
        """
        Пользователь с назначенными PR — список PR'ов
        """
        # создаём команду
        await client.post("/team/add", json=sample_team_data)

        # создаём PR (ревьюверы будут назначены автоматически)
        pr_response = await client.post(
            "/pullRequest/create",
            json={
                "pull_request_id": "pr-1001",
                "pull_request_name": "Add search",
                "author_id": "u1",
            },
        )
        pr_data = pr_response.json()
        assigned_reviewers = pr_data["pr"]["assigned_reviewers"]

        # проверяем что ревьювер видит этот PR
        if assigned_reviewers:
            reviewer_id = assigned_reviewers[0]
            response = await client.get("/users/getReview", params={"user_id": reviewer_id})

            assert response.status_code == 200
            data = response.json()

            assert data["user_id"] == reviewer_id
            assert len(data["pull_requests"]) == 1
            assert data["pull_requests"][0]["pull_request_id"] == "pr-1001"
            assert data["pull_requests"][0]["status"] == "OPEN"

    async def test_get_review_nonexistent_user_returns_empty(self, client: AsyncClient):
        """
        Запрос PR'ов для несуществующего user_id

        По OpenAPI: всегда 200, даже если пользователя нет — просто пустой список
        """
        response = await client.get("/users/getReview", params={"user_id": "nonexistent"})

        assert response.status_code == 200
        data = response.json()
        assert data["user_id"] == "nonexistent"
        assert data["pull_requests"] == []

    async def test_get_review_missing_param_returns_422(self, client: AsyncClient):
        """
        Запрос без параметра user_id — 422 Validation Error
        """
        response = await client.get("/users/getReview")

        assert response.status_code == 422


class TestUserActivation:
    """
    Дополнительные тесты активации/деактивации
    """

    async def test_toggle_is_active_multiple_times(
        self, client: AsyncClient, sample_team_data: dict
    ):
        """
        Множественная смена статуса активности — проверяем идемпотентность
        """
        await client.post("/team/add", json=sample_team_data)

        # деактивируем
        r1 = await client.post("/users/setIsActive", json={"user_id": "u1", "is_active": False})
        assert r1.status_code == 200
        assert r1.json()["user"]["is_active"] is False

        # активируем обратно
        r2 = await client.post("/users/setIsActive", json={"user_id": "u1", "is_active": True})
        assert r2.status_code == 200
        assert r2.json()["user"]["is_active"] is True

        # повторно активируем (уже активен)
        r3 = await client.post("/users/setIsActive", json={"user_id": "u1", "is_active": True})
        assert r3.status_code == 200
        assert r3.json()["user"]["is_active"] is True
