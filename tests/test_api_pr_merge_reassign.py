import pytest


@pytest.mark.asyncio
async def test_merge_idempotent(async_client):
    pr_payload = {
        "pull_request_id": "pr-2001",
        "pull_request_name": "Idempotent merge",
        "author_id": "u1",
    }
    await async_client.post("/pullRequest/create", json=pr_payload)
    merge_payload = {"pull_request_id": "pr-2001"}
    resp1 = await async_client.post("/pullRequest/merge", json=merge_payload)
    resp2 = await async_client.post("/pullRequest/merge", json=merge_payload)
    assert resp1.status_code == 200
    assert resp2.status_code == 200
    assert resp1.json()["pr"]["status"] == "MERGED"
    assert resp2.json()["pr"]["status"] == "MERGED"


@pytest.mark.asyncio
async def test_reassign_reviewer(async_client):
    team_payload = {
        "team_name": "reassigners",
        "members": [
            {"user_id": "u10", "username": "Ann", "is_active": True},
            {"user_id": "u11", "username": "Ben", "is_active": True},
            {"user_id": "u12", "username": "Sam", "is_active": True},
        ],
    }
    await async_client.post("/team/add", json=team_payload)
    pr_payload = {
        "pull_request_id": "pr-3001",
        "pull_request_name": "Reassign test",
        "author_id": "u10",
    }
    await async_client.post("/pullRequest/create", json=pr_payload)
    pr = (await async_client.post("/pullRequest/create", json=pr_payload)).json()["pr"]
    assigned = pr["assigned_reviewers"]
    old_reviewer = assigned[0] if assigned else "u11"
    reassign_payload = {"pull_request_id": "pr-3001", "old_user_id": old_reviewer}
    resp = await async_client.post("/pullRequest/reassign", json=reassign_payload)
    assert resp.status_code == 200
    assert "pr" in resp.json()
    assert "replaced_by" in resp.json()
    assert resp.json()["pr"]["pull_request_id"] == "pr-3001"
