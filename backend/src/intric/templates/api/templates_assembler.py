from typing import TYPE_CHECKING

from intric.templates.api.template_models import TemplateListPublic

if TYPE_CHECKING:
    from intric.templates.app_template.api.app_template_assembler import (
        AppTemplateAssembler,
    )
    from intric.templates.assistant_template.api.assistant_template_assembler import (
        AssistantTemplateAssembler,
    )
    from intric.templates.templates import Templates


class TemplateAssembler:
    def __init__(
        self,
        app_assembler: "AppTemplateAssembler",
        assistant_assembler: "AssistantTemplateAssembler",
    ) -> None:
        self.app_assembler = app_assembler
        self.assistant_assembler = assistant_assembler

    def to_paginated_response(
        self,
        templates: "Templates",
    ) -> TemplateListPublic:
        apps = self.app_assembler.to_paginated_response(templates.app_templates).items

        assistants = self.assistant_assembler.to_paginated_response(
            templates.assistant_templates
        ).items

        # Sort items
        all_items = sorted(
            apps + assistants, key=lambda item: item.created_at, reverse=True
        )

        return TemplateListPublic(items=all_items)
