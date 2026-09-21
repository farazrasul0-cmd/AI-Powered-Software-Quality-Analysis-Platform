"""Repository registration and management endpoints."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.schemas.repository import RepositoryCreate, RepositoryResponse
from app.core.security import is_safe_repository_url
from app.infrastructure.db.models.repository import Repository
from app.infrastructure.db.session import get_db_session
from app.repositories.repository_repo import RepositoryRepo

router = APIRouter(prefix="/repositories", tags=["Repositories"])


@router.post("", response_model=RepositoryResponse, status_code=status.HTTP_201_CREATED)
@router.post("/onboard", response_model=RepositoryResponse, status_code=status.HTTP_201_CREATED)
async def create_repository(
    payload: RepositoryCreate,
    session: AsyncSession = Depends(get_db_session),
):
    is_safe, reason = is_safe_repository_url(payload.url)
    if not is_safe:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Security error: {reason}",
        )

    repo_repo = RepositoryRepo(session)
    existing = await repo_repo.get_by_url(payload.url)
    if existing:
        return existing

    # Derive name if not provided
    name = payload.name
    if not name:
        clean_url = payload.url.rstrip("/")
        if clean_url.endswith(".git"):
            clean_url = clean_url[:-4]
        name = clean_url.split("/")[-1] or "repository"

    repo = Repository(
        url=payload.url,
        name=name,
        default_branch=payload.default_branch,
    )
    return await repo_repo.create(repo)


@router.get("", response_model=list[RepositoryResponse])
async def list_repositories(
    limit: int = 50,
    offset: int = 0,
    session: AsyncSession = Depends(get_db_session),
):
    repo_repo = RepositoryRepo(session)
    return await repo_repo.list_all(limit=limit, offset=offset)


@router.get("/{repo_id}", response_model=RepositoryResponse)
async def get_repository(
    repo_id: str,
    session: AsyncSession = Depends(get_db_session),
):
    repo_repo = RepositoryRepo(session)
    repo = await repo_repo.get_by_id(repo_id)
    if not repo:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Repository not found")
    return repo
