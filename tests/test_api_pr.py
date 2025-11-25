import pytest


@pytest.mark.asyncio
async def test_create_and_merge_pr(async_client):
    pr_payload = {
        "pull_request_id": "pr-1001",
        "pull_request_name": "Add search",
        "author_id": "u1",
    }
    resp = await async_client.post("/pullRequest/create", json=pr_payload)
    assert resp.status_code == 201
    assert "pr" in resp.json()
    pr = resp.json()["pr"]
    assert pr["pull_request_id"] == "pr-1001"
    assert pr["status"] == "OPEN"
    assert len(pr["assigned_reviewers"]) <= 2

    merge_payload = {"pull_request_id": "pr-1001"}
    resp = await async_client.post("/pullRequest/merge", json=merge_payload)
    assert resp.status_code == 200
    pr = resp.json()["pr"]
    assert pr["status"] == "MERGED"
