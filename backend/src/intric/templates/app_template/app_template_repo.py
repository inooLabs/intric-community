from typing import TYPE_CHECKING, Optional

from sqlalchemy.future import select
from sqlalchemy.orm import selectinload

from intric.database.tables.app_template_table import AppTemplates


if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession

    from intric.templates.app_template.app_template import AppTemplate
    from intric.templates.app_template.app_template_factory import (
        AppTemplateFactory,
    )


class AppTemplateRepository:
    def __init__(self, session: "AsyncSession", factory: "AppTemplateFactory"):
        self.session = session
        self.factory = factory

        self._db_model = AppTemplates
        # db relations
        self._options = [selectinload(self._db_model.completion_model)]

    async def get_by_id(self, app_template_id) -> Optional["AppTemplate"]:
        query = (
            select(self._db_model)
            .options(*self._options)
            .where(self._db_model.id == app_template_id)
        )

        record = await self.session.scalar(query)

        if not record:
            return None

        return self.factory.create_app_template(item=record)

    async def get_app_template_list(self) -> list["AppTemplate"]:
        query = select(self._db_model).options(*self._options)
        results = await self.session.scalars(query)

        return self.factory.create_app_template_list(items=results.all())
