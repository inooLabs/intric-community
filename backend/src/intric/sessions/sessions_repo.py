from datetime import datetime
from typing import Optional
from uuid import UUID

import sqlalchemy as sa
from sqlalchemy.orm import selectinload

from intric.database.database import AsyncSession
from intric.database.repositories.base import BaseRepositoryDelegate
from intric.database.tables.assistant_table import Assistants
from intric.database.tables.info_blobs_table import InfoBlobs
from intric.database.tables.questions_table import (
    InfoBlobReferences,
    Questions,
    QuestionsFiles,
)
from intric.database.tables.sessions_table import Sessions
from intric.database.tables.users_table import Users
from intric.sessions.session import (
    SessionAdd,
    SessionFeedback,
    SessionInDB,
    SessionUpdate,
)


class SessionRepository:
    def __init__(self, session: AsyncSession):
        self.delegate = BaseRepositoryDelegate(
            session, Sessions, SessionInDB, with_options=self._options()
        )
        self.session = session

    @staticmethod
    def _options():
        return [
            selectinload(Sessions.questions)
            .selectinload(Questions.info_blob_references)
            .selectinload(InfoBlobReferences.info_blob)
            .selectinload(InfoBlobs.group),
            selectinload(Sessions.questions)
            .selectinload(Questions.info_blob_references)
            .selectinload(InfoBlobReferences.info_blob)
            .selectinload(InfoBlobs.website),
            selectinload(Sessions.questions).selectinload(Questions.logging_details),
            selectinload(Sessions.questions).selectinload(Questions.assistant),
            selectinload(Sessions.questions).selectinload(Questions.completion_model),
            selectinload(Sessions.questions)
            .selectinload(Questions.questions_files)
            .selectinload(QuestionsFiles.file),
            selectinload(Sessions.questions).selectinload(Questions.questions_files),
            selectinload(Sessions.questions).selectinload(Questions.web_search_results),
            selectinload(Sessions.assistant).selectinload(Assistants.user),
        ]

    def _add_options(self, stmt: sa.Select | sa.Insert | sa.Update):
        for option in self._options():
            stmt = stmt.options(option)

        return stmt

    async def add(self, session: SessionAdd) -> SessionInDB:
        return await self.delegate.add(session)

    async def update(self, session: SessionUpdate) -> SessionInDB:
        return await self.delegate.update(session)

    async def add_feedback(self, feedback: SessionFeedback, id: UUID):
        stmt = (
            sa.Update(Sessions)
            .values(feedback_value=feedback.value, feedback_text=feedback.text)
            .where(Sessions.id == id)
            .returning(Sessions)
        )

        stmt_with_options = self._add_options(stmt)
        session = await self.session.scalar(stmt_with_options)

        return SessionInDB.model_validate(session)

    async def get(self, id: Optional[UUID] = None, user_id: UUID = None) -> SessionInDB:
        if id is None and user_id is None:
            raise ValueError("One of id and user_id is required")

        if id is not None:
            return await self.delegate.get(id)

        return await self.delegate.filter_by(conditions={Sessions.user_id: user_id})

    async def _get_total_count(
        self,
        assistant_id: UUID = None,
        user_id: UUID = None,
        group_chat_id: UUID = None,
        start_date: datetime = None,
        end_date: datetime = None,
    ):
        query = sa.select(sa.func.count()).select_from(Sessions)

        if assistant_id is not None:
            query = query.where(Sessions.assistant_id == assistant_id)
        if group_chat_id is not None:
            query = query.where(Sessions.group_chat_id == group_chat_id)

        if user_id is not None:
            query = query.where(Sessions.user_id == user_id)

        if start_date is not None:
            query = query.where(Sessions.created_at >= start_date)

        if end_date is not None:
            query = query.where(Sessions.created_at <= end_date)

        return await self.session.scalar(query)

    async def get_by_assistant(
        self,
        assistant_id: UUID,
        user_id: UUID = None,
        limit: int = None,
        cursor: datetime = None,
        previous: bool = False,
        name_filter: str = None,
        start_date: datetime = None,
        end_date: datetime = None,
    ):
        query = (
            sa.select(Sessions)
            .where(Sessions.assistant_id == assistant_id)
            .order_by(Sessions.created_at.desc())
        )

        if user_id is not None:
            query = query.where(Sessions.user_id == user_id)

        if name_filter is not None:
            query = query.where(Sessions.name.ilike(f"%{name_filter}%"))

        if start_date is not None:
            query = query.where(Sessions.created_at >= start_date)

        if end_date is not None:
            query = query.where(Sessions.created_at <= end_date)

        total_count = await self._get_total_count(
            assistant_id=assistant_id,
            user_id=user_id,
            start_date=start_date,
            end_date=end_date,
        )

        if limit is not None:
            query = query.limit(limit + 1)

        if cursor is not None:
            if previous:
                query = query.order_by(Sessions.created_at.asc()).where(
                    Sessions.created_at > cursor
                )
                items = await self.delegate.get_models_from_query(query)
                return (
                    sorted(items, key=lambda x: x.created_at, reverse=True),
                    total_count,
                )
            else:
                query = query.where(Sessions.created_at <= cursor)

        sessions = await self.delegate.get_models_from_query(query)
        return sessions, total_count

    async def get_by_group_chat(
        self,
        group_chat_id: UUID,
        user_id: UUID = None,
        limit: int = None,
        cursor: datetime = None,
        previous: bool = False,
        name_filter: str = None,
        start_date: datetime = None,
        end_date: datetime = None,
    ):
        query = (
            sa.select(Sessions)
            .where(Sessions.group_chat_id == group_chat_id)
            .order_by(Sessions.created_at.desc())
        )

        if user_id is not None:
            query = query.where(Sessions.user_id == user_id)

        if name_filter is not None:
            query = query.where(Sessions.name.ilike(f"%{name_filter}%"))

        if start_date is not None:
            query = query.where(Sessions.created_at >= start_date)

        if end_date is not None:
            query = query.where(Sessions.created_at <= end_date)

        # don't include name filter to get the true total
        total_count = await self._get_total_count(
            group_chat_id=group_chat_id,
            user_id=user_id,
            start_date=start_date,
            end_date=end_date,
        )

        if limit is not None:
            query = query.limit(limit + 1)

        if cursor is not None:
            if previous:
                query = query.order_by(Sessions.created_at.asc()).where(
                    Sessions.created_at > cursor
                )
                items = await self.delegate.get_models_from_query(query)
                return (
                    sorted(items, key=lambda x: x.created_at, reverse=True),
                    total_count,
                )
            else:
                query = query.where(Sessions.created_at <= cursor)

        sessions = await self.delegate.get_models_from_query(query)
        return sessions, total_count

    async def get_by_tenant(
        self, tenant_id: UUID, start_date: datetime = None, end_date: datetime = None
    ):
        query = sa.select(Sessions).join(Users).where(Users.tenant_id == tenant_id)

        if start_date is not None:
            query = query.filter(Sessions.created_at >= start_date)

        if end_date is not None:
            query = query.filter(Sessions.created_at <= end_date)

        sessions = await self.delegate.get_models_from_query(query)
        return sessions

    async def delete(self, id: int) -> SessionInDB:
        return await self.delegate.delete(id)
