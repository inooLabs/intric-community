from typing import TYPE_CHECKING, Optional
from uuid import UUID

from intric.admin.quota_service import QuotaService
from intric.groups.group_service import GroupService
from intric.info_blobs.info_blob import (
    InfoBlobAdd,
    InfoBlobInDB,
    InfoBlobMetadataFilter,
    InfoBlobMetadataFilterPublic,
    InfoBlobUpdate,
)
from intric.info_blobs.info_blob_repo import InfoBlobRepository
from intric.main.exceptions import (
    NameCollisionException,
    NotFoundException,
    UnauthorizedException,
)
from intric.main.logging import get_logger
from intric.spaces.space import SpacePermissionsActions
from intric.users.user import UserInDB
from intric.websites.website_service import WebsiteService

if TYPE_CHECKING:
    from intric.actors import ActorManager
    from intric.spaces.space_service import SpaceService

logger = get_logger(__name__)


class InfoBlobService:
    def __init__(
        self,
        *,
        repo: InfoBlobRepository,
        user: UserInDB,
        quota_service: QuotaService,
        group_service: GroupService,
        website_service: WebsiteService,
        space_service: "SpaceService",
        actor_manager: "ActorManager",
    ):
        self.repo = repo
        self.group_service = group_service
        self.website_service = website_service
        self.user = user
        self.quota_service = quota_service
        self.space_service = space_service
        self.actor_manager = actor_manager

    async def _get_actor_from_space_id(self, space_id: UUID):
        space = await self.space_service.get_space(space_id)
        return self.actor_manager.get_space_actor_from_space(space)

    async def _can_perform_action_on_group(
        self, group_id: UUID, action: SpacePermissionsActions
    ):
        group = await self.group_service.get_group(group_id)
        actor = await self._get_actor_from_space_id(group.space_id)

        match action:
            case SpacePermissionsActions.READ:
                if not actor.can_read_groups():
                    raise UnauthorizedException()
            case SpacePermissionsActions.EDIT:
                if not actor.can_edit_group(group=group):
                    raise UnauthorizedException()
            case SpacePermissionsActions.DELETE:
                if not actor.can_delete_group(group=group):
                    raise UnauthorizedException()

    async def _can_perform_action(
        self, info_blob: InfoBlobInDB, action: SpacePermissionsActions
    ):
        if info_blob.group_id is not None:
            await self._can_perform_action_on_group(
                group_id=info_blob.group_id, action=action
            )

        if info_blob.website_id is not None:
            website = await self.website_service.get_website(info_blob.website_id)
            actor = await self._get_actor_from_space_id(website.space_id)

            match action:
                case SpacePermissionsActions.READ:
                    if not actor.can_read_websites():
                        raise UnauthorizedException()
                case SpacePermissionsActions.EDIT:
                    if not actor.can_edit_website(website=website):
                        raise UnauthorizedException()
                case SpacePermissionsActions.DELETE:
                    if not actor.can_delete_website(website=website):
                        raise UnauthorizedException()

    async def _validate(
        self,
        info_blob: Optional[InfoBlobInDB],
        action: SpacePermissionsActions = SpacePermissionsActions.READ,
    ):
        if info_blob is None:
            raise NotFoundException("InfoBlob not found")

        await self._can_perform_action(info_blob, action=action)

    async def _delete_if_same_title(self, info_blob: InfoBlobAdd):
        if info_blob.title:
            if info_blob.group_id:
                info_blob_deleted = await self.repo.delete_by_title_and_group(
                    info_blob.title, info_blob.group_id
                )

                if info_blob_deleted is not None:
                    logger.debug(
                        f"Info blob ({info_blob_deleted.title}) in group "
                        f"({info_blob.group_id}) was replaced"
                    )

            elif info_blob.website_id:
                info_blob_deleted = await self.repo.delete_by_title_and_website(
                    info_blob.title, info_blob.website_id
                )

                if info_blob_deleted is not None:
                    logger.debug(
                        f"Info blob ({info_blob_deleted.title}) in website "
                        f"({info_blob.website_id}) was replaced"
                    )

    async def add_info_blob_without_validation(self, info_blob: InfoBlobAdd):
        await self._delete_if_same_title(info_blob)
        size_of_text = await self.quota_service.add_text(info_blob.text)
        info_blob.size = size_of_text
        info_blob_in_db = await self.repo.add(info_blob)

        return info_blob_in_db

    async def add_info_blob(self, info_blob: InfoBlobAdd):
        info_blob_in_db = await self.add_info_blob_without_validation(info_blob)

        await self._validate(info_blob_in_db)

        return info_blob_in_db

    async def add_info_blobs(self, group_id: UUID, info_blobs: list[InfoBlobAdd]):
        # Adding info-blobs to groups is considered editing the group
        await self._can_perform_action_on_group(
            group_id=group_id, action=SpacePermissionsActions.EDIT
        )

        return [await self.add_info_blob(blob) for blob in info_blobs]

    async def update_info_blob(self, info_blob: InfoBlobUpdate):
        current_info_blob = await self.repo.get(info_blob.id)

        if info_blob.title:
            info_blob_with_same_name = await self.repo.get_by_title_and_group(
                info_blob.title, current_info_blob.group.id
            )

            if info_blob_with_same_name is not None:
                raise NameCollisionException(
                    "Info blob with same name already exists in the same group"
                )

        info_blob_updated = await self.repo.update(info_blob)

        await self._validate(info_blob_updated, action=SpacePermissionsActions.EDIT)

        return info_blob_updated

    async def get_by_id(self, id: str):
        blob = await self.repo.get(id)

        await self._validate(blob)

        return blob

    async def get_by_user(self, metadata_filter: InfoBlobMetadataFilter | None = None):
        info_blobs = await self.repo.get_by_user(user_id=self.user.id)

        if metadata_filter:

            def filter_func(item: InfoBlobInDB):
                filter_dict = metadata_filter.model_dump(exclude_none=True)
                item_dict = item.model_dump()
                return filter_dict.items() <= item_dict.items()

            info_blobs = list(filter(filter_func, info_blobs))

        return [blob for blob in info_blobs]

    async def get_by_filter(
        self,
        metadata_filter: InfoBlobMetadataFilterPublic,
    ):
        metadata_filter_with_user = InfoBlobMetadataFilter(
            **metadata_filter.model_dump(), user_id=self.user.id
        )
        return await self.get_by_user(metadata_filter_with_user)

    async def get_by_group(self, id: UUID) -> list[InfoBlobInDB]:
        group = await self.group_service.get_group(id)
        return await self.repo.get_by_group(group.id)

    async def get_by_website(self, id: UUID) -> list[InfoBlobInDB]:
        website = await self.website_service.get_website(id)
        return await self.repo.get_by_website(website.id)

    async def delete(self, id: str):
        info_blob_deleted = await self.repo.delete(id)

        await self._validate(info_blob_deleted, action=SpacePermissionsActions.DELETE)

        return info_blob_deleted
