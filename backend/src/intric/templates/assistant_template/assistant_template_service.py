from typing import TYPE_CHECKING

from intric.main.exceptions import NotFoundException

if TYPE_CHECKING:
    from uuid import UUID
    from intric.templates.assistant_template.assistant_template import AssistantTemplate
    from intric.templates.assistant_template.assistant_template_repo import (
        AssistantTemplateRepository,
    )
    from intric.templates.assistant_template.assistant_template_factory import (
        AssistantTemplateFactory,
    )


class AssistantTemplateService:
    def __init__(
        self,
        factory: "AssistantTemplateFactory",
        repo: "AssistantTemplateRepository",
    ) -> None:
        self.factory = factory
        self.repo = repo

    async def get_assistant_template(
        self, assistant_template_id: "UUID"
    ) -> "AssistantTemplate":
        assistant_template = await self.repo.get_by_id(
            assistant_template_id=assistant_template_id
        )

        if assistant_template is None:
            raise NotFoundException()

        return assistant_template

    async def get_assistant_templates(self) -> list["AssistantTemplate"]:
        return await self.repo.get_assistant_template_list()
