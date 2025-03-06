from datetime import datetime
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest

from intric.main.exceptions import BadRequestException, UnauthorizedException
from intric.spaces.api.space_models import SpaceRoleValue
from intric.spaces.space_service import SpaceService
from tests.fixtures import TEST_USER, TEST_UUID, TEST_TENANT, TEST_MODEL_GPT4, TEST_MODEL_CHATGPT, TEST_EMBEDDING_MODEL, TEST_EMBEDDING_MODEL_ADA
from intric.securitylevels.security_level import SecurityLevel
from intric.spaces.space import Space
from intric.ai_models.completion_models.completion_model import CompletionModelPublic
from intric.ai_models.embedding_models.embedding_model import EmbeddingModelPublic
@pytest.fixture
def actor():
    return MagicMock()


@pytest.fixture
def service(actor: MagicMock):
    actor_manager = MagicMock()
    actor_manager.get_space_actor_from_space.return_value = actor

    service = SpaceService(
        repo=AsyncMock(),
        completion_model_crud_service=AsyncMock(),
        factory=MagicMock(),
        user_repo=AsyncMock(),
        ai_models_service=AsyncMock(),
        security_level_service=AsyncMock(),
        user=TEST_USER,
        actor_manager=actor_manager,
    )

    return service


async def test_create_space_is_created_with_latest_available_embedding_model(
    service: SpaceService,
):
    space = MagicMock()
    embedding_models = [
        MagicMock(created_at=datetime(2024, 1, 3 - i), can_access=True)
        for i in range(3)
    ]
    service.factory.create_space.return_value = space
    service.ai_models_service.get_embedding_models.return_value = embedding_models

    await service.create_space(MagicMock())

    assert space.embedding_models == [embedding_models[0]]


async def test_raise_not_found_if_user_not_member_of_space(
    service: SpaceService, actor: MagicMock
):
    actor.can_read_space.return_value = False

    with pytest.raises(UnauthorizedException):
        await service.get_space(uuid4())


async def test_raise_unauthorized_if_user_can_not_edit(
    service: SpaceService, actor: MagicMock
):
    actor.can_edit_space.return_value = False

    with pytest.raises(UnauthorizedException):
        await service.update_space(uuid4(), MagicMock())


async def test_raise_unauthorized_if_user_can_not_delete(
    service: SpaceService, actor: MagicMock
):
    actor.can_delete_space.return_value = False

    with pytest.raises(UnauthorizedException):
        await service.delete_space(uuid4())


async def test_only_admins_can_add_members(service: SpaceService, actor: MagicMock):
    actor.can_edit_space.return_value = False

    service.user_repo.get_user_by_id_and_tenant_id.return_value = MagicMock(
        email="test@test.com", username="username"
    )

    with pytest.raises(UnauthorizedException):
        await service.add_member(MagicMock(), MagicMock(), role=SpaceRoleValue.EDITOR)


async def test_only_admins_can_delete_members(service: SpaceService, actor: MagicMock):
    actor.can_edit_space.return_value = False

    with pytest.raises(UnauthorizedException):
        await service.remove_member(MagicMock(), MagicMock())


async def test_can_not_remove_self(service: SpaceService):
    id = uuid4()
    service.user = MagicMock(id=id)

    with pytest.raises(BadRequestException):
        await service.remove_member(MagicMock(), id)


async def test_only_admins_can_change_role_of_member(
    service: SpaceService, actor: MagicMock
):
    actor.can_edit_space.return_value = False

    with pytest.raises(UnauthorizedException):
        await service.change_role_of_member(MagicMock(), MagicMock(), MagicMock())


async def test_can_not_change_role_of_self(service: SpaceService):
    id = uuid4()
    service.user = MagicMock(id=id)

    with pytest.raises(BadRequestException):
        await service.change_role_of_member(MagicMock(), id, MagicMock())


async def test_get_personal_space_returns_all_available_completion_models(
    service: SpaceService,
):
    personal_space = MagicMock()
    completion_models = [MagicMock(), MagicMock()]
    service.repo.get_personal_space.return_value = personal_space
    service.completion_model_crud_service.get_available_completion_models.return_value = (
        completion_models
    )

    space = await service.get_personal_space()

    assert space.completion_models == completion_models


async def test_get_personal_space_returns_all_available_embedding_models(
    service: SpaceService,
):
    personal_space = MagicMock()
    embedding_models = [MagicMock(), MagicMock()]
    service.repo.get_personal_space.return_value = personal_space
    service.ai_models_service.get_embedding_models.return_value = embedding_models

    space = await service.get_personal_space()

    assert space.embedding_models == embedding_models


async def test_get_spaces_and_personal_space_returns_personal_space_first(
    service: SpaceService,
):
    personal_space = MagicMock()
    other_spaces = [MagicMock(), MagicMock(), MagicMock()]

    service.repo.get_personal_space.return_value = personal_space
    service.repo.get_spaces_for_member.return_value = other_spaces

    spaces = await service.get_spaces(include_personal=True)

    assert spaces == [personal_space] + other_spaces


@pytest.fixture
def security_level():
    return SecurityLevel(
        id=TEST_UUID,
        tenant_id=TEST_TENANT.id,
        name="test_level",
        description="Test security level",
        value=100,
        created_at="2024-01-01T00:00:00",
        updated_at="2024-01-01T00:00:00",
    )


@pytest.fixture
def higher_security_level():
    return SecurityLevel(
        id=uuid4(),
        tenant_id=TEST_TENANT.id,
        name="high_level",
        description="High security level",
        value=200,
        created_at="2024-01-01T00:00:00",
        updated_at="2024-01-01T00:00:00",
    )


async def test_update_space_security_level(
    service: SpaceService, security_level: SecurityLevel
):
    """Test updating a space's security level."""
    space = MagicMock()
    space.can_edit.return_value = True

    service.get_space = AsyncMock(return_value=space)
    service.security_level_service.get_security_level = AsyncMock(return_value=security_level)
    service.ai_models_service.get_completion_models = AsyncMock(return_value=[])
    service.ai_models_service.get_embedding_models = AsyncMock(return_value=[])

    await service.update_space(
        id=TEST_UUID,
        security_level_id=security_level.id,
    )

    # Check that update was called with the security level
    space.update.assert_called_once_with(
        name=None,
        description=None,
        completion_models=[],
        embedding_models=[],
        security_level=security_level,
    )

async def test_update_space_with_inaccessible_models_raises_unauthorized(service: SpaceService):
    """
    Test that validates that the behavior of updating a space with inaccessible models raises UnauthorizedException.
    TODO: Verify that this is not a bug. When a model is deactivated on the organization and still activated on a space, the space can not toggle any of the other models.
    """
    # Create a real Space instance
    space = Space(
        id=TEST_UUID,
        tenant_id=TEST_UUID,
        user_id=None,
        name="Test Space",
        description=None,
        embedding_models=[],
        completion_models=[],
        assistants=[],
        services=[],
        websites=[],
        groups=[],
        members={TEST_USER.id: MagicMock(role=SpaceRoleValue.ADMIN)},
        default_assistant=None,
        apps=[],
    )

    # Create a mix of accessible and inaccessible models
    accessible_model = MagicMock(can_access=True, id=uuid4())
    inaccessible_model = MagicMock(can_access=False, id=uuid4())
    models = [accessible_model, inaccessible_model]

    service.get_space = AsyncMock(return_value=space)
    service.ai_models_service.get_completion_models = AsyncMock(return_value=models)

    # Verify that attempting to update with inaccessible models raises UnauthorizedException
    with pytest.raises(UnauthorizedException):
        await service.update_space(
            id=TEST_UUID,
            completion_model_ids=[accessible_model.id, inaccessible_model.id]
        )

async def test_analyze_update_shows_unavailable_completion_models(service: SpaceService):
    """Test that analyze_update shows unavailable completion models."""
    security_level_low = SecurityLevel(
        id=TEST_UUID,
        tenant_id=TEST_UUID,
        name="Security Level Low",
        description="Test security level low",
        value=1,
    )
    security_level_high = SecurityLevel(
        id=uuid4(),
        tenant_id=TEST_UUID,
        name="Security Level High",
        description="Test security level high",
        value=2,
    )
    completion_model_low = TEST_MODEL_GPT4
    completion_model_low.security_level_id = security_level_low.id
    completion_model_high = TEST_MODEL_CHATGPT
    completion_model_high.security_level_id = security_level_high.id

    space = Space(
        id=TEST_UUID,
        tenant_id=TEST_UUID,
        user_id=None,
        name="Test Space",
        description=None,
        embedding_models=[],
        completion_models=[completion_model_low],
        assistants=[],
        services=[],
        websites=[],
        groups=[],
        members={TEST_USER.id: MagicMock(role=SpaceRoleValue.ADMIN)},
        default_assistant=None,
        apps=[],
        security_level=security_level_low,
    )

    completion_model_low_public = CompletionModelPublic(
        **completion_model_low.model_dump(),
        is_locked=False,
        can_access=True,
        security_level=security_level_low,
    )

    service.get_space = AsyncMock(return_value=space)
    service.security_level_service.get_security_level = AsyncMock(return_value=security_level_high)
    service.ai_models_service.get_completion_models = AsyncMock(return_value=[completion_model_low_public])

    analysis = await service.analyze_update(TEST_UUID, security_level_id=security_level_high.id)

    service.get_space.assert_called_with(TEST_UUID)
    service.ai_models_service.get_completion_models.assert_called_with(id_list=[completion_model_low.id])
    service.security_level_service.get_security_level.assert_called_with(security_level_high.id)
    assert service.ai_models_service.get_completion_models.call_count == 1

    assert analysis.unavailable_completion_models == [completion_model_low_public]
    assert analysis.unavailable_embedding_models == []
    assert analysis.new_security_level == security_level_high

async def test_analyze_update_shows_unavailable_embedding_models(service: SpaceService):
    """Test that analyze_update shows unavailable embedding models."""
    security_level_low = SecurityLevel(
        id=TEST_UUID,
        tenant_id=TEST_UUID,
        name="Security Level Low",
        description="Test security level low",
        value=1,
    )
    security_level_high = SecurityLevel(
        id=uuid4(),
        tenant_id=TEST_UUID,
        name="Security Level High",
        description="Test security level high",
        value=2,
    )
    embedding_model_low = TEST_EMBEDDING_MODEL
    embedding_model_low.security_level_id = security_level_low.id
    embedding_model_high = TEST_EMBEDDING_MODEL_ADA
    embedding_model_high.security_level_id = security_level_high.id

    space = Space(
        id=TEST_UUID,
        tenant_id=TEST_UUID,
        user_id=None,
        name="Test Space",
        description=None,
        embedding_models=[embedding_model_low],
        completion_models=[],
        assistants=[],
        services=[],
        websites=[],
        groups=[],
        members={TEST_USER.id: MagicMock(role=SpaceRoleValue.ADMIN)},
        default_assistant=None,
        apps=[],
        security_level=security_level_low,
    )

    embedding_model_low_public = EmbeddingModelPublic(
        **embedding_model_low.model_dump(),
        is_locked=False,
        can_access=True,
        security_level=security_level_low,
    )

    service.get_space = AsyncMock(return_value=space)
    service.security_level_service.get_security_level = AsyncMock(return_value=security_level_high)
    service.ai_models_service.get_embedding_model = AsyncMock(return_value=embedding_model_low_public)

    analysis = await service.analyze_update(TEST_UUID, security_level_id=security_level_high.id)

    service.get_space.assert_called_with(TEST_UUID)
    service.security_level_service.get_security_level.assert_called_with(security_level_high.id)
    service.ai_models_service.get_embedding_model.assert_called_with(embedding_model_low.id, include_non_accessible=True)

    assert analysis.unavailable_completion_models == []
    assert analysis.unavailable_embedding_models == [embedding_model_low]
    assert analysis.new_security_level == security_level_high
