import pytest


@pytest.mark.asyncio
async def test_get_review(async_client):
    resp = await async_client.get("/users/getReview", params={"user_id": "u2"})
    assert resp.status_code == 200
    data = resp.json()
    assert "user_id" in data
    assert "pull_requests" in data
    assert isinstance(data["pull_requests"], list)
