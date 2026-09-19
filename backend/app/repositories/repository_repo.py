"""Repository database operations."""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.db.models.repository import Repository


class RepositoryRepo:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_by_id(self, repo_id: str) -> Repository | None:
        result = await self.session.execute(select(Repository).where(Repository.id == repo_id))
        return result.scalar_one_or_none()

    async def get_by_url(self, url: str) -> Repository | None:
        result = await self.session.execute(select(Repository).where(Repository.url == url))
        return result.scalar_one_or_none()

    async def list_all(self, limit: int = 50, offset: int = 0) -> list[Repository]:
        result = await self.session.execute(
            select(Repository).order_by(Repository.created_at.desc()).limit(limit).offset(offset)
        )
        return list(result.scalars().all())

    async def create(self, repo: Repository) -> Repository:
        self.session.add(repo)
        await self.session.flush()
        return repo
