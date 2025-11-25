import pytest


@pytest.mark.asyncio
async def test_add_and_get_team(async_client):
    team_payload = {
        "team_name": "backend",
        "members": [
            {"user_id": "u1", "username": "Alice", "is_active": True},
            {"user_id": "u2", "username": "Bob", "is_active": True},
        ],
    }
    resp = await async_client.post("/team/add", json=team_payload)
    assert resp.status_code == 201
    assert "team" in resp.json()
    team = resp.json()["team"]
    assert team["team_name"] == "backend"
    assert len(team["members"]) == 2

    resp = await async_client.get("/team/get", params={"team_name": "backend"})
    assert resp.status_code == 200
    assert resp.json()["team_name"] == "backend"
