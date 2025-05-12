from typing import TYPE_CHECKING, Optional

from intric.collections.domain.collection import Collection
from intric.main.exceptions import UnauthorizedException

if TYPE_CHECKING:
    from uuid import UUID

    from intric.actors.actor_manager import ActorManager
    from intric.spaces.space_repo import SpaceRepository
    from intric.spaces.space_service import SpaceService
    from intric.users.user import UserInDB


class CollectionCRUDService:
    def __init__(
        self,
        user: "UserInDB",
        space_service: "SpaceService",
        space_repo: "SpaceRepository",
        actor_manager: "ActorManager",
    ):
        self.user = user
        self.space_service = space_service
        self.space_repo = space_repo
        self.actor_manager = actor_manager

    async def create_collection(
        self,
        space_id: "UUID",
        name: str,
        embedding_model_id: Optional["UUID"] = None,
    ) -> Collection:
        space = await self.space_service.get_space(space_id)
        actor = self.actor_manager.get_space_actor_from_space(space=space)

        if not actor.can_create_collections():
            raise UnauthorizedException()

        if embedding_model_id is None:
            embedding_model = space.get_default_embedding_model()
        else:
            embedding_model = space.get_embedding_model(embedding_model_id)

        collection = Collection.create(
            space_id=space.id,
            user=self.user,
            name=name,
            embedding_model=embedding_model,
        )

        space.add_collection(collection)
        updated_space = await self.space_repo.update(space=space)
        new_collection = updated_space.get_collection(collection_id=collection.id)

        return new_collection

    async def get_collection(self, collection_id: "UUID") -> Collection:
        space = await self.space_service.get_space_by_collection(collection_id)
        actor = self.actor_manager.get_space_actor_from_space(space=space)

        if not actor.can_read_collections():
            raise UnauthorizedException()

        return space.get_collection(collection_id=collection_id)

    async def update_collection(
        self,
        collection_id: "UUID",
        name: str,
    ) -> Collection:
        space = await self.space_service.get_space_by_collection(collection_id)
        actor = self.actor_manager.get_space_actor_from_space(space=space)

        if not actor.can_edit_collections():
            raise UnauthorizedException()

        collection = space.get_collection(collection_id=collection_id)
        collection.update(name=name)

        updated_space = await self.space_repo.update(space=space)
        return updated_space.get_collection(collection_id=collection_id)

    async def delete_collection(self, collection_id: "UUID") -> None:
        space = await self.space_service.get_space_by_collection(collection_id)
        actor = self.actor_manager.get_space_actor_from_space(space=space)

        if not actor.can_delete_collections():
            raise UnauthorizedException()

        collection = space.get_collection(collection_id=collection_id)
        space.remove_collection(collection)
        await self.space_repo.update(space=space)
