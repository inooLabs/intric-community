from uuid import UUID

import sqlalchemy as sa
from sqlalchemy.orm import defer

from intric.database.database import AsyncSession
from intric.database.repositories.base import (
    BaseRepositoryDelegate,
    worker_transaction,
)
from intric.database.tables.files_table import Files
from intric.files.file_models import File, FileCreate, FileInfo


class FileRepository:
    def __init__(self, session: AsyncSession):
        self._delegate = BaseRepositoryDelegate(
            session=session, table=Files, in_db_model=File
        )
        self.session = session

    async def add(self, file: FileCreate) -> File:
        return await self._delegate.add(file)

    @worker_transaction
    async def get_list_by_id_and_user(self, ids: list[UUID], user_id: UUID) -> list[File]:
        stmt = (
            sa.select(Files)
            .where(Files.id.in_(ids))
            .where(Files.user_id == user_id)
            .order_by(Files.created_at)
        )

        files_in_db = await self.session.scalars(stmt)

        return [File.model_validate(file) for file in files_in_db]

    async def get_by_id(self, file_id: UUID) -> File:
        file = await self._delegate.get(id=file_id)
        return File.model_validate(file)

    async def get_list_by_user(self, user_id: UUID) -> File:
        return await self._delegate.filter_by(conditions={Files.user_id: user_id})

    async def get_by_checksum(self, checksum: str) -> File:
        return await self._delegate.get_by(conditions={Files.checksum: checksum})

    async def delete(self, id: UUID) -> File:
        return await self._delegate.delete(id)

    async def get_file_infos(self, ids: list[UUID]) -> list[FileInfo]:
        stmt = (
            sa.select(Files)
            .where(Files.id.in_(ids))
            .options(
                defer(Files.text, raiseload=True), defer(Files.blob, raiseload=True)
            )
        )

        files_in_db = await self.session.scalars(stmt)

        return [FileInfo.model_validate(file) for file in files_in_db]
