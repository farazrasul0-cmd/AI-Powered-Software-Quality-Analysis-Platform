"""Integration tests for FastAPI REST Endpoints."""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_health_check(async_client: AsyncClient):
    response = await async_client.get("/api/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "version" in data


@pytest.mark.asyncio
async def test_create_and_list_repositories(async_client: AsyncClient):
    # 1. Create a repository
    payload = {
        "url": "https://github.com/octocat/Hello-World.git",
        "name": "Octocat Hello World",
        "default_branch": "master",
    }
    create_res = await async_client.post("/api/v1/repositories", json=payload)
    assert create_res.status_code == 201
    repo_data = create_res.json()
    assert repo_data["name"] == "Octocat Hello World"
    assert repo_data["url"] == payload["url"]
    repo_id = repo_data["id"]

    # 2. List repositories
    list_res = await async_client.get("/api/v1/repositories")
    assert list_res.status_code == 200
    repos = list_res.json()
    assert len(repos) >= 1
    assert any(r["id"] == repo_id for r in repos)

    # 3. Get single repository
    get_res = await async_client.get(f"/api/v1/repositories/{repo_id}")
    assert get_res.status_code == 200
    assert get_res.json()["id"] == repo_id


@pytest.mark.asyncio
async def test_trigger_analysis_job(async_client: AsyncClient):
    # Create repository first
    repo_res = await async_client.post(
        "/api/v1/repositories",
        json={"url": "https://github.com/psf/requests.git", "default_branch": "main"},
    )
    repo_id = repo_res.json()["id"]

    # Trigger analysis
    trigger_res = await async_client.post(
        "/api/v1/analysis/trigger",
        json={"repository_id": repo_id, "branch": "main"},
    )
    assert trigger_res.status_code == 202
    job_data = trigger_res.json()
    assert job_data["repository_id"] == repo_id
    assert job_data["status"] == "QUEUED"
    job_id = job_data["id"]

    # Query status
    status_res = await async_client.get(f"/api/v1/analysis/jobs/{job_id}")
    assert status_res.status_code == 200
    assert status_res.json()["id"] == job_id
