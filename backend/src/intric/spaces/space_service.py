# Copyright (c) 2024 Sundsvalls Kommun
#
# Licensed under the MIT License.

from dataclasses import dataclass
from typing import Optional
from uuid import UUID

from intric.ai_models.ai_models_service import AIModelsService
from intric.ai_models.completion_models.completion_model import CompletionModelPublic, CompletionModelSparse
from intric.ai_models.embedding_models.embedding_model import EmbeddingModelPublic, EmbeddingModelSparse
from intric.main.exceptions import (
    BadRequestException,
    NotFoundException,
    UnauthorizedException,
)
from intric.securitylevels.security_level import SecurityLevel
from intric.securitylevels.security_level_service import SecurityLevelService
from intric.spaces.api.space_models import SpaceMember, SpaceRoleValue
from intric.spaces.space import Space
from intric.spaces.space_factory import SpaceFactory
from intric.spaces.space_repo import SpaceRepository
from intric.users.user import UserInDB
from intric.users.user_repo import UsersRepository

@dataclass
class SpaceUpdateAnalysis:
    """Analysis of the impact of updating a space's properties."""

    def __init__(
        self,
        current_security_level: Optional[SecurityLevel],
        new_security_level: Optional[SecurityLevel],
        unavailable_completion_models: list[CompletionModelPublic],
        unavailable_embedding_models: list[EmbeddingModelPublic],
    ):
        self.current_security_level = current_security_level
        self.new_security_level = new_security_level
        self.unavailable_completion_models = unavailable_completion_models
        self.unavailable_embedding_models = unavailable_embedding_models


class SpaceService:
    def __init__(
        self,
        user: UserInDB,
        factory: SpaceFactory,
        repo: SpaceRepository,
        user_repo: UsersRepository,
        ai_models_service: AIModelsService,
        completion_model_crud_service: "CompletionModelCRUDService",
        actor_manager: "ActorManager",
        security_level_service: SecurityLevelService,
    ):
        self.user = user
        self.factory = factory
        self.repo = repo
        self.user_repo = user_repo
        self.ai_models_service = ai_models_service
        self.completion_model_crud_service = completion_model_crud_service
        self.actor_manager = actor_manager
        self.security_level_service = security_level_service

    def _get_actor(self, space: Space):
        return self.actor_manager.get_space_actor_from_space(space)

    async def _add_models_to_personal_space(self, personal_space: Space):
        def _available_models(
            models: list[CompletionModelPublic | EmbeddingModelPublic],
        ):
            return [model for model in models if model.can_access]

        available_completion_models = (
            await self.completion_model_crud_service.get_available_completion_models()
        )
        available_embedding_models = _available_models(
            await self.ai_models_service.get_embedding_models()
        )

        personal_space.completion_models = available_completion_models
        personal_space.embedding_models = available_embedding_models

        return personal_space

    async def create_space(self, name: str):
        space = self.factory.create_space(name=name)

        def _get_latest_model(models):
            for model in sorted(
                models, key=lambda model: model.created_at, reverse=True
            ):
                if model.can_access:
                    return model

        # Set embedding models as only the latest one
        embedding_models = await self.ai_models_service.get_embedding_models()
        latest_model = _get_latest_model(embedding_models)
        space.embedding_models = [latest_model] if latest_model else []

        # Set completion models
        completion_models = (
            await self.completion_model_crud_service.get_available_completion_models()
        )
        space.completion_models = completion_models

        # Set tenant
        space.tenant_id = self.user.tenant_id

        # Set admin
        admin = SpaceMember(
            id=self.user.id,
            username=self.user.username,
            email=self.user.email,
            role=SpaceRoleValue.ADMIN,
        )
        space.add_member(admin)

        return await self.repo.add(space)

    async def get_space(self, id: UUID) -> Space:
        space = await self.repo.one(id)

        actor = self._get_actor(space)
        if not actor.can_read_space():
            raise UnauthorizedException()

        if space.is_personal():
            space = await self._add_models_to_personal_space(space)

        return space

    async def _get_filtered_model_ids(
        self,
        current_models: list[CompletionModelSparse | EmbeddingModelSparse],
        unavailable_models: list[CompletionModelSparse | EmbeddingModelSparse]
    ) -> list[UUID]:
        """Helper to get IDs of models that will remain available."""
        unavailable_ids = {model.id for model in unavailable_models}
        return [model.id for model in current_models if model.id not in unavailable_ids]

    async def update_space(
        self,
        id: UUID,
        name: Optional[str] = None,
        description: Optional[str] = None,
        embedding_model_ids: Optional[list[UUID]] = None,
        completion_model_ids: Optional[list[UUID]] = None,
        security_level_id: Optional[UUID] = None,
    ) -> Space:
        """Update a space."""
        space = await self.get_space(id)
        actor = self._get_actor(space)

        if not actor.can_edit_space():
            raise UnauthorizedException("User does not have permission to edit space")

        update_kwargs = {
            "name": name,
            "description": description,
            "security_level": None if security_level_id is None else await self.security_level_service.get_security_level(security_level_id)
        }

        # If security level is changing, analyze impact on models
        if security_level_id is not None and (space.security_level is None or security_level_id != space.security_level.id):
            analysis = await self.analyze_update(id, security_level_id)

            # If no explicit model IDs provided, filter out incompatible models
            if completion_model_ids is None:
                completion_model_ids = await self._get_filtered_model_ids(
                    space.completion_models,
                    analysis.unavailable_completion_models
                )
            if embedding_model_ids is None:
                embedding_model_ids = await self._get_filtered_model_ids(
                    space.embedding_models,
                    analysis.unavailable_embedding_models
                )

        # Fetch and set models if IDs are provided (either explicitly or from filtering)
        if completion_model_ids is not None:
            # Get full Public models
            update_kwargs["completion_models"] = await self.ai_models_service.get_completion_models(
                id_list=completion_model_ids,
            )
        if embedding_model_ids is not None:
            # Get full Public models
            update_kwargs["embedding_models"] = await self.ai_models_service.get_embedding_models(
                id_list=embedding_model_ids,
            )

        space.update(**update_kwargs)
        return await self.repo.update(space)

    async def delete_personal_space(self, user: UserInDB):
        space = await self.repo.get_personal_space(user.id)

        if space is not None:
            await self.repo.delete(space.id)

    async def delete_space(self, id: UUID):
        space = await self.get_space(id)
        actor = self._get_actor(space)

        if not actor.can_delete_space():
            raise UnauthorizedException("User does not have permission to delete space")

        await self.repo.delete(space.id)

    async def get_spaces(self, *, include_personal: bool = False) -> list[Space]:
        spaces = await self.repo.get_spaces_for_member(self.user.id)

        if include_personal:
            personal_space = await self.get_personal_space()
            return [personal_space] + spaces

        return spaces

    async def add_member(self, id: UUID, member_id: UUID, role: SpaceRoleValue):
        space = await self.get_space(id)
        actor = self._get_actor(space)

        if not actor.can_edit_space():
            raise UnauthorizedException("Only Admins of the space can add members")

        user = await self.user_repo.get_user_by_id_and_tenant_id(
            id=member_id, tenant_id=self.user.tenant_id
        )

        if user is None:
            raise NotFoundException("User not found")

        member = SpaceMember(
            id=member_id,
            username=user.username,
            email=user.email,
            role=role,
        )

        space.add_member(member)
        space = await self.repo.update(space)

        return space.get_member(member.id)

    async def remove_member(self, id: UUID, user_id: UUID):
        if user_id == self.user.id:
            raise BadRequestException("Can not remove yourself")

        space = await self.get_space(id)
        actor = self._get_actor(space)

        if not actor.can_edit_space():
            raise UnauthorizedException("Only Admins of the space can remove members")

        space.remove_member(user_id)

        await self.repo.update(space)

    async def change_role_of_member(
        self, id: UUID, user_id: UUID, new_role: SpaceRoleValue
    ):
        if user_id == self.user.id:
            raise BadRequestException("Can not change role of yourself")

        space = await self.get_space(id)
        actor = self._get_actor(space)

        if not actor.can_edit_space():
            raise UnauthorizedException(
                "Only Admins of the space can change the roles of members"
            )

        space.change_member_role(user_id, new_role)
        space = await self.repo.update(space)

        return space.get_member(user_id)

    async def create_personal_space(self):
        space_name = f"{self.user.username}'s personal space"
        space = self.factory.create_space(name=space_name, user_id=self.user.id)

        # Set tenant
        space.tenant_id = self.user.tenant_id

        space_in_db = await self.repo.add(space)

        return await self._add_models_to_personal_space(space_in_db)

    async def get_personal_space(self):
        personal_space = await self.repo.get_personal_space(self.user.id)

        if personal_space is None:
            return

        return await self._add_models_to_personal_space(personal_space)

    async def _get_unavailable_models_for_security_level(
        self,
        models: list[CompletionModelSparse | EmbeddingModelSparse],
        new_security_level: Optional[SecurityLevel],
        get_full_model_fn
    ) -> list[CompletionModelSparse | EmbeddingModelSparse]:
        """Helper to find models that will become unavailable with new security level."""
        unavailable = []
        for model in models:
            full_model = await get_full_model_fn(model.id, include_non_accessible=True)
            if not full_model.security_level or (
                new_security_level
                and full_model.security_level.value < new_security_level.value
            ):
                unavailable.append(model)
        return unavailable

    async def analyze_update(
        self,
        id: UUID,
        security_level_id: Optional[UUID] = None,
    ) -> SpaceUpdateAnalysis:
        """
        Analyze the impact of updating a space's properties without actually applying the changes.
        Currently supports:
        - Security level changes: Shows which models would be affected
        """
        space = await self.get_space(id)
        new_security_level = None
        if security_level_id is not None:
            new_security_level = await self.security_level_service.get_security_level(security_level_id)

        # Check which models will be affected
        unavailable_completion_models = []
        for model in space.completion_models:
            # Get the full model from the list of all models
            all_models = await self.ai_models_service.get_completion_models(id_list=[model.id])
            if not all_models:
                continue
            full_model = all_models[0]
            if not full_model.security_level or (
                new_security_level
                and full_model.security_level.value < new_security_level.value
            ):
                unavailable_completion_models.append(full_model)

        unavailable_embedding_models = await self._get_unavailable_models_for_security_level(
            space.embedding_models,
            new_security_level,
            self.ai_models_service.get_embedding_model
        )

        return SpaceUpdateAnalysis(
            current_security_level=space.security_level,
            new_security_level=new_security_level,
            unavailable_completion_models=unavailable_completion_models,
            unavailable_embedding_models=unavailable_embedding_models,
        )
