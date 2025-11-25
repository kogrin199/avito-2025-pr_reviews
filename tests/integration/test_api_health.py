"""
Интеграционные тесты для /health
"""

from httpx import AsyncClient


class TestHealth:
    """
    Тесты GET /health
    """

    async def test_health_check(self, client: AsyncClient):
        """
        Health check возвращает 200
        """
        response = await client.get("/health")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
