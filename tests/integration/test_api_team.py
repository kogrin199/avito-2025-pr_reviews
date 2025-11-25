"""
Интеграционные тесты для API команд (/team/*)

Тестируемые эндпоинты по OpenAPI:
- POST /team/add — создание команды
- GET /team/get — получение команды
"""

from httpx import AsyncClient


class TestTeamAdd:
    """
    Тесты POST /team/add
    """

    async def test_create_team_success(self, client: AsyncClient, sample_team_data: dict):
        """
        Успешное создание команды — 201
        """
        response = await client.post("/team/add", json=sample_team_data)

        assert response.status_code == 201
        data = response.json()

        assert "team" in data
        team = data["team"]
        assert team["team_name"] == sample_team_data["team_name"]
        assert len(team["members"]) == len(sample_team_data["members"])

        # проверяем что все участники на месте
        member_ids = {m["user_id"] for m in team["members"]}
        expected_ids = {m["user_id"] for m in sample_team_data["members"]}
        assert member_ids == expected_ids

    async def test_create_team_duplicate_returns_400(
        self, client: AsyncClient, sample_team_data: dict
    ):
        """
        повторное создание команды — 400 TEAM_EXISTS
        """
        # создаём первый раз
        response1 = await client.post("/team/add", json=sample_team_data)
        assert response1.status_code == 201

        # пытаемся создать повторно
        response2 = await client.post("/team/add", json=sample_team_data)

        assert response2.status_code == 400
        data = response2.json()
        assert data["detail"]["error"]["code"] == "TEAM_EXISTS"

    async def test_create_team_with_inactive_member(
        self, client: AsyncClient, sample_team_with_inactive: dict
    ):
        """
        Можно создать команду с неактивными участниками
        """
        response = await client.post("/team/add", json=sample_team_with_inactive)

        assert response.status_code == 201
        data = response.json()

        # проверяем что неактивный участник сохранён
        members = data["team"]["members"]
        inactive = [m for m in members if not m["is_active"]]
        assert len(inactive) == 1
        assert inactive[0]["user_id"] == "f2"


class TestTeamGet:
    """
    Тесты GET /team/get
    """

    async def test_get_team_success(self, client: AsyncClient, sample_team_data: dict):
        """
        Успешное получение существующей команды — 200
        """
        # сначала создаём команду
        await client.post("/team/add", json=sample_team_data)

        # получаем
        response = await client.get(
            "/team/get", params={"team_name": sample_team_data["team_name"]}
        )

        assert response.status_code == 200
        data = response.json()

        assert data["team_name"] == sample_team_data["team_name"]
        assert len(data["members"]) == len(sample_team_data["members"])

    async def test_get_team_not_found_returns_404(self, client: AsyncClient):
        """
        Запрос несуществующей команды — 404 NOT_FOUND
        """
        response = await client.get("/team/get", params={"team_name": "nonexistent"})

        assert response.status_code == 404
        data = response.json()
        assert data["detail"]["error"]["code"] == "NOT_FOUND"

    async def test_get_team_missing_param_returns_422(self, client: AsyncClient):
        """
        Запрос без параметра team_name — 422 Validation Error
        """
        response = await client.get("/team/get")

        assert response.status_code == 422


class TestTeamMembers:
    """
    Дополнительные тесты для участников команды
    """

    async def test_team_members_have_correct_fields(self, client: AsyncClient):
        """
        Проверяем что участники команды имеют все поля
        """
        team_data = {
            "team_name": "fields_team",
            "members": [
                {"user_id": "ft1", "username": "FieldTest1", "is_active": True},
            ],
        }
        await client.post("/team/add", json=team_data)

        response = await client.get("/team/get", params={"team_name": "fields_team"})
        assert response.status_code == 200

        member = response.json()["members"][0]
        assert member["user_id"] == "ft1"
        assert member["username"] == "FieldTest1"
        assert member["is_active"] is True
