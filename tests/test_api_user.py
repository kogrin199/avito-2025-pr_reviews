import pytest


@pytest.mark.asyncio
async def test_set_is_active(async_client):
    payload = {"user_id": "u2", "is_active": False}
    resp = await async_client.post("/users/setIsActive", json=payload)
    assert resp.status_code == 200
    assert "user" in resp.json()
    user = resp.json()["user"]
    assert user["user_id"] == "u2"
    assert user["is_active"] is False
