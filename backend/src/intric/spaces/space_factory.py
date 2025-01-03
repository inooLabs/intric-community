from typing import TYPE_CHECKING

from intric.ai_models.completion_models.completion_model import CompletionModel
from intric.ai_models.embedding_models.embedding_model import EmbeddingModel
from intric.assistants.api.assistant_models import AssistantSparse
from intric.database.tables.ai_models_table import CompletionModels, EmbeddingModels
from intric.database.tables.groups_table import Groups
from intric.database.tables.spaces_table import Spaces
from intric.groups.group import GroupMetadata, GroupSparse
from intric.main.models import IdAndName
from intric.services.service import ServiceSparse
from intric.spaces.api.space_models import AppSparse, SpaceMember
from intric.spaces.space import Space
from intric.websites.website_models import WebsiteSparse

if TYPE_CHECKING:
    from uuid import UUID

    from intric.assistants.assistant import Assistant


class SpaceFactory:

    @staticmethod
    def create_space(
        name: str, description: str = None, user_id: "UUID" = None
    ) -> Space:
        return Space(
            id=None,
            tenant_id=None,
            user_id=user_id,
            name=name,
            description=description,
            embedding_models=[],
            completion_models=[],
            default_assistant=None,
            assistants=[],
            apps=[],
            services=[],
            websites=[],
            groups=[],
            members={},
        )

    @staticmethod
    def create_space_from_db(
        space_in_db: Spaces,
        groups_in_db: list[tuple[Groups, int]] = [],
        completion_models_in_db: list[tuple[CompletionModels, bool]] = [],
        embedding_models_in_db: list[tuple[EmbeddingModels, bool]] = [],
        default_assistant: "Assistant" = None,
    ) -> Space:
        completion_models = [
            CompletionModel(**model.to_dict(), is_org_enabled=is_org_enabled)
            for model, is_org_enabled in completion_models_in_db
        ]
        embedding_models = [
            EmbeddingModel(**model.to_dict(), is_org_enabled=is_org_enabled)
            for model, is_org_enabled in embedding_models_in_db
        ]
        members = {
            space_user.user_id: SpaceMember(
                **space_user.user.to_dict(), role=space_user.role
            )
            for space_user in space_in_db.members
            if space_user.user.deleted_at is None
        }
        groups = [
            GroupSparse(
                **group.to_dict(),
                metadata=GroupMetadata(num_info_blobs=info_blob_count),
                embedding_model=IdAndName.model_validate(group.embedding_model)
            )
            for group, info_blob_count in groups_in_db
        ]
        assistants = [
            AssistantSparse.model_validate(assistant)
            for assistant in space_in_db.assistants
            if not assistant.is_default
        ]
        apps = [AppSparse.model_validate(app) for app in space_in_db.apps]
        services = [
            ServiceSparse.model_validate(service) for service in space_in_db.services
        ]
        websites = [
            WebsiteSparse.model_validate(website) for website in space_in_db.websites
        ]

        # Set the tools of the default assistant
        if default_assistant is not None:
            default_assistant.tool_assistants = assistants

        return Space(
            created_at=space_in_db.created_at,
            updated_at=space_in_db.updated_at,
            id=space_in_db.id,
            tenant_id=space_in_db.tenant_id,
            user_id=space_in_db.user_id,
            name=space_in_db.name,
            description=space_in_db.description,
            embedding_models=embedding_models,
            default_assistant=default_assistant,
            assistants=assistants,
            apps=apps,
            services=services,
            groups=groups,
            websites=websites,
            completion_models=completion_models,
            members=members,
        )
