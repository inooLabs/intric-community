from datetime import datetime
from enum import Enum
from typing import TYPE_CHECKING
from uuid import UUID

from intric.ai_models.completion_models.completion_model import (
    CompletionModel,
    CompletionModelPublic,
)
from intric.ai_models.embedding_models.embedding_model import (
    EmbeddingModel,
    EmbeddingModelPublic,
)
from intric.assistants.api.assistant_models import AssistantSparse
from intric.groups.group import GroupSparse
from intric.main.exceptions import BadRequestException, UnauthorizedException
from intric.services.service import ServiceSparse
from intric.spaces.api.space_models import AppSparse, SpaceMember, SpaceRole
from intric.websites.website_models import WebsiteSparse

if TYPE_CHECKING:
    from intric.assistants.assistant import Assistant

UNAUTHORIZED_EXCEPTION_MESSAGE = "Unauthorized. User has no permissions to access."


class SpacePermissionsActions(Enum):
    READ = "read"
    EDIT = "edit"
    DELETE = "delete"


class Space:
    def __init__(
        self,
        id: UUID | None,
        tenant_id: UUID | None,
        user_id: UUID | None,
        name: str,
        description: str | None,
        embedding_models: list[EmbeddingModel],
        completion_models: list[CompletionModel],
        default_assistant: "Assistant",
        assistants: list[AssistantSparse],
        apps: list[AppSparse],
        services: list[ServiceSparse],
        websites: list[WebsiteSparse],
        groups: list[GroupSparse],
        members: dict[UUID, SpaceMember],
        created_at: datetime = None,
        updated_at: datetime = None,
    ):
        self.id = id
        self.tenant_id = tenant_id
        self.user_id = user_id
        self.name = name
        self.description = description
        self._embedding_models = embedding_models
        self._completion_models = completion_models
        self.default_assistant = default_assistant
        self.assistants = assistants
        self.apps = apps
        self.services = services
        self.websites = websites
        self.groups = groups
        self.members = members
        self.created_at = created_at
        self.updated_at = updated_at

    def _get_member_ids(self):
        return self.members.keys()

    def is_personal(self):
        return self.user_id is not None

    def is_embedding_model_in_space(self, embedding_model_id: UUID | None) -> bool:
        return self.is_personal() or embedding_model_id in [
            model.id for model in self.embedding_models
        ]

    def is_completion_model_in_space(self, completion_model_id: UUID | None) -> bool:
        return self.is_personal() or completion_model_id in [
            model.id for model in self.completion_models
        ]

    def is_group_in_space(self, group_id: UUID) -> bool:
        return group_id in [group.id for group in self.groups]

    def is_website_in_space(self, website_id: UUID) -> bool:
        return website_id in [website.id for website in self.websites]

    def get_member(self, member_id: UUID) -> SpaceMember:
        return self.members[member_id]

    def get_latest_embedding_model(self) -> EmbeddingModel:
        if not self.embedding_models:
            return

        sorted_embedding_models = sorted(
            self.embedding_models, key=lambda model: model.created_at, reverse=True
        )

        return sorted_embedding_models[0]

    def get_latest_completion_model(self) -> CompletionModel:
        if not self.completion_models:
            return

        sorted_completion_models = sorted(
            self.completion_models, key=lambda model: model.created_at, reverse=True
        )

        return sorted_completion_models[0]

    def get_default_model(self) -> CompletionModel | None:
        if not self.completion_models:
            return None

        DEFAULT_MODEL = "gpt-4o"
        model = filter(
            lambda m: m.name == DEFAULT_MODEL and m.can_access, self.completion_models
        )
        return next(model, None)

    @property
    def embedding_models(self):
        return self._embedding_models

    @embedding_models.setter
    def embedding_models(self, embedding_models: list[EmbeddingModelPublic]):
        for model in embedding_models:
            if not model.can_access:
                raise UnauthorizedException(UNAUTHORIZED_EXCEPTION_MESSAGE)

        self._embedding_models = embedding_models

    @property
    def completion_models(self) -> list[CompletionModelPublic]:
        return self._completion_models

    @completion_models.setter
    def completion_models(self, completion_models: list[CompletionModelPublic]):
        for model in completion_models:
            if not model.can_access:
                raise UnauthorizedException(UNAUTHORIZED_EXCEPTION_MESSAGE)

        self._completion_models = completion_models

    def update(
        self,
        name: str = None,
        description: str = None,
        embedding_models: list[EmbeddingModelPublic] = None,
        completion_models: list[CompletionModelPublic] = None,
    ):
        if name is not None:
            if self.is_personal():
                raise BadRequestException("Can not change name of personal space")

            self.name = name

        if description is not None:
            if self.is_personal():
                raise BadRequestException(
                    "Can not change description of personal space"
                )

            self.description = description

        if completion_models is not None:
            if self.is_personal():
                raise BadRequestException(
                    "Can not add completion models to personal space"
                )

            self.completion_models = completion_models

        if embedding_models is not None:
            if self.is_personal():
                raise BadRequestException(
                    "Can not add embedding models to personal space"
                )

            self.embedding_models = embedding_models

    def add_member(self, user: SpaceMember):
        if self.is_personal():
            raise BadRequestException("Can not add members to personal space")

        if user.id in self._get_member_ids():
            raise BadRequestException("User is already a member of the space")

        self.members[user.id] = user

    def remove_member(self, user_id: UUID):
        if user_id not in self._get_member_ids():
            raise BadRequestException("User is not a member of the space")

        del self.members[user_id]

    def change_member_role(self, user_id: UUID, new_role: SpaceRole):
        if user_id not in self._get_member_ids():
            raise BadRequestException("User is not a member of the space")

        self.members[user_id].role = new_role
