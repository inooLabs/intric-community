from typing import TYPE_CHECKING

import sqlalchemy as sa

from intric.database.tables.assistant_table import AssistantsWebsites

if TYPE_CHECKING:
    from uuid import UUID

    from intric.database.database import AsyncSession


class WebsiteCleanerService:
    def __init__(self, session: "AsyncSession"):
        self.session = session

    async def remove_website_from_all_assistants(
        self, website_id: "UUID", assistant_ids: list["UUID"]
    ):
        stmt = (
            sa.delete(AssistantsWebsites)
            .where(AssistantsWebsites.website_id == website_id)
            .where(
                AssistantsWebsites.assistant_id.not_in(assistant_ids),
            )
        )

        await self.session.execute(stmt)
