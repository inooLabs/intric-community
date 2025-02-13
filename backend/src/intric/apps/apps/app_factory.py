from typing import TYPE_CHECKING, Optional

from intric.ai_models.completion_models.completion_model import (
    CompletionModel,
    CompletionModelSparse,
    ModelKwargs,
)
from intric.apps.apps.api.app_models import InputField, InputFieldType
from intric.apps.apps.app import App
from intric.database.tables.app_table import Apps
from intric.files.file_models import File
from intric.prompts.prompt import Prompt
from intric.spaces.space import Space
from intric.users.user import UserInDB

if TYPE_CHECKING:
    from intric.files.file_models import FileInfo
    from intric.templates.app_template.app_template import AppTemplate
    from intric.templates.app_template.app_template_factory import AppTemplateFactory


class AppFactory:
    def __init__(self, app_template_factory: "AppTemplateFactory"):
        self.app_template_factory = app_template_factory

    def create_app(
        self, user: UserInDB, space: Space, name: str, completion_model: CompletionModel
    ):
        return App(
            created_at=None,
            updated_at=None,
            id=None,
            user_id=user.id,
            tenant_id=user.tenant_id,
            space_id=space.id,
            name=name,
            description=None,
            prompt=None,
            completion_model=completion_model,
            completion_model_kwargs=None,
            input_fields=[
                InputField(type=InputFieldType.TEXT_FIELD)
            ],  # default input fields
            attachments=[],
            published=False,
        )

    def create_app_from_template(
        self,
        user: "UserInDB",
        template: "AppTemplate",
        space: Space,
        completion_model: CompletionModel,
        input_fields: list[InputField],
        name: str | None = None,
        prompt: Prompt | None = None,
        attachments: Optional[list["FileInfo"]] = None,
    ) -> App:
        app = App(
            user_id=user.id,
            tenant_id=user.tenant_id,
            space_id=space.id,
            name=name or template.name,
            description=template.description,
            prompt=prompt,
            attachments=attachments or [],
            completion_model_kwargs=ModelKwargs(**template.completion_model_kwargs),
            input_fields=input_fields,
            created_at=None,
            updated_at=None,
            id=None,
            completion_model=completion_model,
            published=False,
            source_template=template,
        )

        return app

    def create_app_from_db(
        self,
        app_in_db: Apps,
        prompt: Prompt = None,
    ):
        completion_model = CompletionModelSparse.model_validate(
            app_in_db.completion_model
        )
        input_fields = [
            InputField.model_validate(input_field)
            for input_field in app_in_db.input_fields
        ]
        attachments = [
            File(**attachment.file.to_dict()) for attachment in app_in_db.attachments
        ]
        model_kwargs = (
            ModelKwargs(**app_in_db.completion_model_kwargs)
            if app_in_db.completion_model_kwargs is not None
            else None
        )

        source_template = (
            self.app_template_factory.create_app_template(app_in_db.template)
            if app_in_db.template
            else None
        )

        return App(
            created_at=app_in_db.created_at,
            updated_at=app_in_db.updated_at,
            id=app_in_db.id,
            space_id=app_in_db.space_id,
            user_id=app_in_db.user_id,
            tenant_id=app_in_db.tenant_id,
            name=app_in_db.name,
            description=app_in_db.description,
            prompt=prompt,
            completion_model=completion_model,
            completion_model_kwargs=model_kwargs,
            input_fields=input_fields,
            attachments=attachments,
            published=app_in_db.published,
            source_template=source_template,
        )
