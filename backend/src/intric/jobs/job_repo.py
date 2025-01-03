from uuid import UUID

import sqlalchemy as sa

from intric.database.database import AsyncSession
from intric.database.repositories.base import BaseRepositoryDelegate
from intric.database.tables.job_table import Jobs
from intric.jobs.job_models import Job, JobInDb, JobUpdate
from intric.main.models import Status


class JobRepository:
    def __init__(self, session: AsyncSession):
        self.delegate = BaseRepositoryDelegate(
            session,
            Jobs,
            JobInDb,
        )

    async def add_job(self, job: Job):
        return await self.delegate.add(job)

    async def update_job(self, id: UUID, job: JobUpdate):
        stmt = (
            sa.update(Jobs)
            .values(job.model_dump(exclude_unset=True))
            .where(Jobs.id == id)
            .returning(Jobs)
        )

        return await self.delegate.get_model_from_query(stmt)

    async def get_job(self, id: UUID):
        return await self.delegate.get_by(conditions={Jobs.id: id})

    async def get_jobs(self, user_id: UUID, include_completed: bool):
        stmt = sa.select(Jobs).where(Jobs.user_id == user_id).order_by(Jobs.created_at)

        if not include_completed:
            stmt = stmt.where(Jobs.status != Status.COMPLETE)

        return await self.delegate.get_models_from_query(stmt)
