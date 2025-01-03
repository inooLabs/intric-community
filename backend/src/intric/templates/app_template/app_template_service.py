from typing import TYPE_CHECKING

from intric.main.exceptions import NotFoundException
from intric_prop.apps.apps.api.app_models import InputField, InputFieldType

if TYPE_CHECKING:
    from uuid import UUID
    from intric.templates.app_template.app_template import AppTemplate
    from intric.templates.app_template.app_template_repo import (
        AppTemplateRepository,
    )
    from intric.templates.app_template.app_template_factory import (
        AppTemplateFactory,
    )


class AppTemplateService:
    def __init__(
        self,
        factory: "AppTemplateFactory",
        repo: "AppTemplateRepository",
    ) -> None:
        self.factory = factory
        self.repo = repo

    async def get_app_template(self, app_template_id: "UUID") -> "AppTemplate":
        app_template = await self.repo.get_by_id(app_template_id=app_template_id)

        if app_template is None:
            raise NotFoundException()

        return app_template

    async def get_app_templates(self) -> list["AppTemplate"]:
        return await self.repo.get_app_template_list()

    def from_template_input_type_to_input_fields(
        self,
        template: "AppTemplate",
    ) -> list[InputField]:
        # TODO: migrate this to a pydantic model
        mapper = {
            "Picture": [
                InputField(
                    type=InputFieldType.IMAGE_UPLOAD,
                    description=template.input_description,
                )
            ],
            "Record Voice": [
                InputField(
                    type=InputFieldType.AUDIO_RECORDER,
                    description=template.input_description,
                )
            ],
            "Text Document": [
                InputField(
                    type=InputFieldType.TEXT_UPLOAD,
                    description=template.input_description,
                )
            ],
        }
        return mapper[template.input_type]
