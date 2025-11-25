import pytest


@pytest.mark.asyncio
async def test_team_exists_error(async_client):
    team_payload = {
        "team_name": "backend",
        "members": [
            {"user_id": "u1", "username": "Alice", "is_active": True},
        ],
    }
    resp = await async_client.post("/team/add", json=team_payload)
    assert resp.status_code == 201
    resp = await async_client.post("/team/add", json=team_payload)
    assert resp.status_code == 400
    assert resp.json()["error"]["code"] == "TEAM_EXISTS"


@pytest.mark.asyncio
async def test_user_not_found_error(async_client):
    payload = {"user_id": "not_exist", "is_active": True}
    resp = await async_client.post("/users/setIsActive", json=payload)
    assert resp.status_code == 404
    assert resp.json()["error"]["code"] == "NOT_FOUND"


@pytest.mark.asyncio
async def test_pr_not_found_error(async_client):
    resp = await async_client.post("/pullRequest/merge", json={"pull_request_id": "not_exist"})
    assert resp.status_code == 404
    assert resp.json()["error"]["code"] == "NOT_FOUND"
