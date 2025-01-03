from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest

from intric.groups.group import GroupUpdatePublic
from intric.groups.group_service import GroupService
from intric.main.exceptions import NotFoundException, UnauthorizedException
from tests.fixtures import TEST_USER, TEST_UUID


@pytest.fixture
def service():
    repo = AsyncMock()
    tenant_repo = AsyncMock()
    info_blob_repo = AsyncMock()

    return GroupService(
        user=TEST_USER,
        repo=repo,
        tenant_repo=tenant_repo,
        info_blob_repo=info_blob_repo,
        ai_models_service=AsyncMock(),
        space_service=AsyncMock(),
        actor_manager=MagicMock(),
        task_service=AsyncMock(),
    )


async def test_get_exception_with_nonexistant_group(service: GroupService):
    service.repo.get_group.return_value = None
    service.repo.update_group.return_value = None
    service.repo.delete_group_by_id.return_value = None

    group_update = GroupUpdatePublic(name="new_name")

    with pytest.raises(NotFoundException, match="not found"):
        await service.get_group(1)

    with pytest.raises(NotFoundException, match="not found"):
        await service.update_group(group_update, id=uuid4())

    with pytest.raises(NotFoundException, match="not found"):
        await service.delete_group(1)


async def test_update_space_group_not_member(service: GroupService):
    group_update = GroupUpdatePublic(name="new name")

    actor = MagicMock()
    actor.can_edit_group.return_value = False
    service.actor_manager.get_space_actor_from_space.return_value = actor

    with pytest.raises(UnauthorizedException):
        await service.update_group(group_update, TEST_UUID)


async def test_update_space_group_member(service: GroupService):
    group_update = GroupUpdatePublic(name="new name")

    await service.update_group(group_update, TEST_UUID)


async def test_delete_space_group_not_member(service: GroupService):
    actor = MagicMock()
    actor.can_delete_group.return_value = False
    service.actor_manager.get_space_actor_from_space.return_value = actor

    with pytest.raises(UnauthorizedException):
        await service.delete_group(TEST_UUID)


async def test_delete_space_group_member(service: GroupService):
    await service.delete_group(TEST_UUID)
