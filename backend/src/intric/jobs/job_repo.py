from datetime import datetime, timedelta, timezone
from uuid import UUID

import sqlalchemy as sa
from arq.jobs import JobStatus

from intric.database.database import AsyncSession
from intric.database.repositories.base import BaseRepositoryDelegate
from intric.database.tables.job_table import Jobs
from intric.jobs.job_manager import job_manager
from intric.jobs.job_models import Job, JobInDb, JobUpdate


class JobRepository:
    def __init__(self, session: AsyncSession):
        self.delegate = BaseRepositoryDelegate(
            session,
            Jobs,
            JobInDb,
        )
        self._job_manager = job_manager

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

    async def get_running_jobs(self, user_id: UUID):
        one_week_ago = datetime.now(timezone.utc) - timedelta(weeks=1)

        stmt = (
            sa.select(Jobs)
            .where(Jobs.user_id == user_id)
            .where(Jobs.created_at >= one_week_ago)
            .order_by(Jobs.created_at)
        )

        jobs_db = await self.delegate.get_models_from_query(stmt)

        running_jobs = [
            job
            for job in jobs_db
            if await self._job_manager.get_job_status(job.id)
            not in [JobStatus.not_found, JobStatus.complete]
        ]

        return running_jobs
