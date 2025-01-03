from copy import deepcopy
from dataclasses import dataclass
from typing import Any
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest
from pydantic import ValidationError

from intric.ai_models.ai_models_service import AIModelsService
from intric.assistants.api.assistant_models import (
    AskAssistant,
    AssistantBase,
    AssistantCreatePublic,
    AssistantUpdatePublic,
)
from intric.assistants.assistant_service import AssistantService
from intric.main.config import get_settings
from intric.main.exceptions import BadRequestException, UnauthorizedException
from intric.main.models import ModelId
from intric.prompts.api.prompt_models import PromptCreate
from tests.fixtures import (
    TEST_ASSISTANT,
    TEST_GROUP,
    TEST_MODEL_GPT4,
    TEST_USER,
    TEST_UUID,
)


@dataclass
class Setup:
    assistant: AssistantBase
    service: AssistantService
    group_service: AsyncMock


@pytest.fixture(name="setup")
def setup_fixture():
    repo = AsyncMock()
    user = TEST_USER
    auth_service = MagicMock()
    assistant = AssistantCreatePublic(
        name="test_name",
        prompt=PromptCreate(text="test_prompt"),
        space_id=TEST_UUID,
        completion_model=ModelId(id=TEST_MODEL_GPT4.id),
    )

    ai_models_service = AIModelsService(
        user=TEST_USER,
        embedding_model_repo=AsyncMock(),
        completion_model_repo=AsyncMock(),
        tenant_repo=AsyncMock(),
    )

    service = AssistantService(
        repo,
        user,
        auth_service,
        AsyncMock(),
        AsyncMock(),
        ai_models_service=ai_models_service,
        group_service=AsyncMock(),
        website_service=AsyncMock(),
        space_service=AsyncMock(),
        factory=MagicMock(),
        prompt_service=AsyncMock(),
        file_service=AsyncMock(),
        assistant_template_service=AsyncMock(),
        session_service=AsyncMock(),
        actor_manager=MagicMock(),
    )

    setup = Setup(assistant=assistant, service=service, group_service=AsyncMock())

    return setup


@pytest.fixture
async def assistant_service():
    return AssistantService(
        repo=AsyncMock(),
        user=MagicMock(id=uuid4()),
        auth_service=MagicMock(),
        service_repo=AsyncMock(),
        step_repo=AsyncMock(),
        ai_models_service=AsyncMock(),
        group_service=AsyncMock(),
        website_service=AsyncMock(),
        space_service=AsyncMock(),
        factory=AsyncMock(),
        prompt_repo=AsyncMock(),
    )


def with_two_different_groups(setup: Setup, attr: str, value_1: Any, value_2: Any):
    group_1 = deepcopy(TEST_GROUP)
    group_2 = deepcopy(TEST_GROUP)

    setattr(group_1, attr, value_1)
    setattr(group_2, attr, value_2)

    assistant = deepcopy(TEST_ASSISTANT)
    assistant.groups = [group_1, group_2]

    setup.service.repo.add.return_value = assistant
    setup.service.repo.update.return_value = assistant
    setup.service.user.id = 1
    setup.service.user.tenant_id = 1


async def test_create_assistant_with_logging_fails_without_compliance_permission(
    setup: Setup,
):
    setup.service.user = MagicMock()
    setup.service.user.permissions = {}
    setup.assistant.logging_enabled = True
    with pytest.raises(UnauthorizedException):
        await setup.service.create_assistant(setup.assistant)


async def test_create_public_assistant_fails_when_not_deployer(setup: Setup):
    setup.service.user = MagicMock()
    setup.service.user.permissions = {}
    with pytest.raises(UnauthorizedException):
        await setup.service.create_assistant(setup.assistant)


async def test_ask_assistant_model():
    files_number = get_settings().max_in_question + 1
    files = [ModelId(id=uuid4()) for _ in range(files_number)]

    with pytest.raises(ValidationError):
        AskAssistant(question="test", files=files)


async def test_update_space_assistant_not_member(setup: Setup):
    assistant_update = AssistantUpdatePublic(name="new name!")

    actor = MagicMock()
    actor.can_edit_assistant.return_value = False
    setup.service.actor_manager.get_space_actor_from_space.return_value = actor

    with pytest.raises(UnauthorizedException):
        await setup.service.update_assistant(assistant_update, TEST_UUID)


async def test_update_space_assistant_member(setup: Setup):
    assistant_update = AssistantUpdatePublic(name="new name!")

    await setup.service.update_assistant(assistant_update, TEST_UUID)


async def test_delete_space_assistant_not_member(setup: Setup):
    actor = MagicMock()
    actor.can_delete_assistant.return_value = False
    setup.service.actor_manager.get_space_actor_from_space.return_value = actor

    with pytest.raises(UnauthorizedException):
        await setup.service.delete_assistant(TEST_UUID)


async def test_delete_space_assistant_member(setup: Setup):
    await setup.service.delete_assistant(TEST_UUID)


async def test_update_assistant_completion_model_not_in_space(setup: Setup):
    space = MagicMock()
    space.is_completion_model_in_space.return_value = False
    setup.service.space_service.get_space.return_value = space

    with pytest.raises(
        BadRequestException,
        match="Completion model is not in space.",
    ):
        await setup.service.update_assistant(TEST_UUID)


async def test_update_assistant_completion_model_in_space(setup: Setup):
    space = MagicMock()
    space.is_completion_model_in_space.return_value = True
    setup.service.space_service.get_space.return_value = space
    setup.service.repo.update.return_value = MagicMock(prompt="new prompt!", id=uuid4())

    await setup.service.update_assistant(TEST_UUID)


async def test_update_assistant_group_not_in_space(setup: Setup):
    space = MagicMock()
    space.is_group_in_space.return_value = False
    setup.service.space_service.get_space.return_value = space

    assistant = MagicMock(groups=[MagicMock()])
    setup.service.repo.get_by_id.return_value = assistant

    with pytest.raises(
        BadRequestException,
        match="Group is not in space.",
    ):
        await setup.service.update_assistant(id=TEST_UUID, name="new name!")


async def test_update_assistant_group_in_space(setup: Setup):
    space = MagicMock()
    space.is_group_in_space.return_value = True
    setup.service.space_service.get_space.return_value = space

    assistant = MagicMock(groups=[MagicMock()], prompt="new prompt!", id=uuid4())
    setup.service.repo.update.return_value = assistant

    await setup.service.update_assistant(TEST_UUID)


async def test_update_assistant_website_not_in_space(setup: Setup):
    space = MagicMock()
    space.is_website_in_space.return_value = False
    setup.service.space_service.get_space.return_value = space

    assistant = MagicMock(websites=[MagicMock()])
    setup.service.repo.get_by_id.return_value = assistant

    with pytest.raises(
        BadRequestException,
        match="Website is not in space.",
    ):
        await setup.service.update_assistant(TEST_UUID)


async def test_update_assistant_website_in_space(setup: Setup):
    space = MagicMock()
    space.is_website_in_space.return_value = True
    setup.service.space_service.get_space.return_value = space

    assistant = MagicMock(websites=[MagicMock()], prompt="new prompt!", id=uuid4())
    setup.service.repo.update.return_value = assistant

    await setup.service.update_assistant(TEST_UUID)


async def test_completion_model_disabled_in_space(setup: Setup):
    assistant = MagicMock(completion_model_id=uuid4(), space_id=uuid4())
    setup.service.repo.get_by_id.return_value = assistant
    space = MagicMock()
    space.is_completion_model_in_space.return_value = False
    setup.service.space_service.get_space.return_value = space

    with pytest.raises(BadRequestException):
        await setup.service.ask(question="hello", assistant_id=MagicMock())


async def test_group_embedding_model_disabled_in_space(setup: Setup):
    assistant = MagicMock(
        space_id=uuid4(),
        groups=[MagicMock(embedding_model_id=uuid4())],
        websites=[],
    )
    setup.service.repo.get_by_id.return_value = assistant

    space = MagicMock()
    space.is_embedding_model_in_space.return_value = False
    setup.service.space_service.get_space.return_value = space

    with pytest.raises(BadRequestException):
        await setup.service.ask(question="hello", assistant_id=MagicMock())


async def test_website_embedding_model_disabled_in_space(setup: Setup):
    assistant = MagicMock(
        space_id=uuid4(),
        websites=[MagicMock(embedding_model_id=uuid4())],
        groups=[],
    )
    setup.service.repo.get_by_id.return_value = assistant

    space = MagicMock()
    space.is_embedding_model_in_space.return_value = False
    setup.service.space_service.get_space.return_value = space

    with pytest.raises(BadRequestException):
        await setup.service.ask(question="hello", assistant_id=MagicMock())
