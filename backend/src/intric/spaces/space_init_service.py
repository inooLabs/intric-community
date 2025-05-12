from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from uuid import UUID

    from intric.assistants.assistant_service import AssistantService
    from intric.spaces.space import Space
    from intric.spaces.space_repo import SpaceRepository
    from intric.spaces.space_service import SpaceService
    from intric.users.user import UserInDB


class SpaceInitService:
    def __init__(
        self,
        user: "UserInDB",
        space_service: "SpaceService",
        assistant_service: "AssistantService",
        space_repo: "SpaceRepository",
    ):
        self.user = user
        self.space_service = space_service
        self.assistant_service = assistant_service
        self.space_repo = space_repo

    async def _update_space_with_default_assistant(self, space: "Space"):
        default_assistant = await self.assistant_service.create_default_assistant("Default", space)
        space.add_assistant(default_assistant)
        return await self.space_repo.update(space)

    async def _create_personal_space(self):
        personal_space = await self.space_service.create_personal_space()
        return await self._update_space_with_default_assistant(personal_space)

    async def create_space(self, name: str):
        space = await self.space_service.create_space(name)
        return await self._update_space_with_default_assistant(space)

    async def get_personal_space(self):
        personal_space = await self.space_service.get_personal_space()

        if personal_space is None:
            # Create personal space if it does not exist
            personal_space = await self._create_personal_space()

        if personal_space.default_assistant is None:
            # Create default assistant if it does not exist
            personal_space = await self._update_space_with_default_assistant(personal_space)

        return personal_space

    async def get_space(self, space_id: "UUID"):
        space = await self.space_service.get_space(space_id)

        if space.default_assistant is None:
            space = await self._update_space_with_default_assistant(space)

        return space
