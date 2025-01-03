from datetime import datetime, timedelta
from unittest.mock import MagicMock
from uuid import uuid4

import pytest

from intric.ai_models.completion_models.completion_model import (
    CompletionModel,
    CompletionModelFamily,
    ModelHostingLocation,
    ModelKwargs,
    ModelStability,
)
from intric.ai_models.embedding_models.embedding_model import (
    EmbeddingModel,
    EmbeddingModelFamily,
)
from intric.assistants.api.assistant_models import AssistantSparse, DefaultAssistant
from intric.files.file_models import FileRestrictions, Limit
from intric.groups.group import GroupMetadata, GroupSparse
from intric.main.models import IdAndName, PaginatedPermissions, ResourcePermission
from intric.questions.question import Tools
from intric.services.service import ServiceSparse
from intric.spaces.api.space_assembler import SpaceAssembler
from intric.spaces.api.space_models import (
    Applications,
    AppSparse,
    Knowledge,
    SpaceMember,
    SpacePublic,
    SpaceRole,
)
from intric.spaces.space import Space
from intric.websites.website_models import WebsiteSparse
from tests.fixtures import (
    TEST_EMBEDDING_MODEL,
    TEST_MODEL_CHATGPT,
    TEST_MODEL_GPT4,
    TEST_USER,
    TEST_UUID,
)

TEST_NAME = "test_name"
TEST_ASSISTANT_SPARSE = AssistantSparse(
    id=TEST_UUID, name=TEST_NAME, published=False, prompt="", user_id=TEST_UUID
)
TEST_SERVICE = ServiceSparse(id=TEST_UUID, name=TEST_NAME, prompt="", user_id=TEST_UUID)
TEST_GROUP = GroupSparse(
    id=TEST_UUID,
    name=TEST_NAME,
    metadata=GroupMetadata(num_info_blobs=10),
    user_id=TEST_UUID,
    embedding_model=IdAndName(id=TEST_UUID, name=TEST_NAME),
    published=False,
)
TEST_WEBSITE = WebsiteSparse(
    id=TEST_UUID,
    name=TEST_NAME,
    url="www.example.com",
    user_id=TEST_UUID,
    embedding_model=IdAndName(id=TEST_UUID, name=TEST_NAME),
    published=False,
)
TEST_DEFAULT_ASSISTANT = DefaultAssistant(
    id=TEST_UUID,
    name=TEST_NAME,
    space_id=TEST_UUID,
    completion_model_kwargs=ModelKwargs(),
    logging_enabled=False,
    attachments=[],
    allowed_attachments=FileRestrictions(
        accepted_file_types=[], limit=Limit(max_files=0, max_size=0)
    ),
    groups=[],
    websites=[],
    completion_model=TEST_MODEL_CHATGPT,
    user=TEST_USER,
    tools=Tools(assistants=[]),
)


@pytest.fixture
def space_assembler():
    assistant_assembler = MagicMock()
    assistant_assembler.from_assistant_to_default_assistant_model.return_value = (
        TEST_DEFAULT_ASSISTANT
    )
    return SpaceAssembler(
        MagicMock(), assistant_assembler=assistant_assembler, actor_manager=MagicMock()
    )


@pytest.fixture
def space():
    space = MagicMock(
        id=TEST_UUID,
        user_id=None,
        tenant_id=TEST_UUID,
        description=None,
        embedding_models=[],
        completion_models=[],
        assistants=[],
        services=[],
        websites=[],
        groups=[],
        members={},
    )
    space.name = TEST_NAME

    return space


# TODO: Review this type of test, since getting the exact shape
# of pydantic test objects is a hassle
def test_from_space_to_model(space_assembler: SpaceAssembler):
    test_name = "test_name"
    now = datetime.now()

    embedding_model = EmbeddingModel(
        id=TEST_UUID,
        name=test_name,
        family=EmbeddingModelFamily.E5,
        is_deprecated=False,
        open_source=True,
        stability=ModelStability.EXPERIMENTAL,
        hosting=ModelHostingLocation.EU,
        is_org_enabled=True,
    )
    completion_model = CompletionModel(
        id=TEST_UUID,
        name=test_name,
        nickname=test_name,
        family=CompletionModelFamily.AZURE,
        token_limit=100,
        is_deprecated=False,
        stability=ModelStability.STABLE,
        hosting=ModelHostingLocation.USA,
        vision=True,
        is_org_enabled=True,
    )
    assistant = AssistantSparse(
        id=TEST_UUID,
        name=test_name,
        published=False,
        prompt="",
        user_id=TEST_UUID,
        permissions=[ResourcePermission.EDIT, ResourcePermission.DELETE],
    )
    service = ServiceSparse(
        id=TEST_UUID,
        name=test_name,
        prompt="",
        user_id=TEST_UUID,
        permissions=[ResourcePermission.EDIT, ResourcePermission.DELETE],
    )
    tenant_id = TEST_UUID
    admin = SpaceMember(
        id=TEST_UUID,
        email="admin@example.com",
        username="admin",
        role=SpaceRole.ADMIN,
        created_at=now,
    )
    editor = SpaceMember(
        id=uuid4(),
        email="editor@example.com",
        username="editor",
        role=SpaceRole.EDITOR,
        created_at=now + timedelta(seconds=1),
    )

    expected_space = SpacePublic(
        created_at=now,
        updated_at=now,
        id=TEST_UUID,
        name=test_name,
        description=None,
        personal=False,
        embedding_models=[embedding_model],
        completion_models=[completion_model],
        default_assistant=TEST_DEFAULT_ASSISTANT,
        applications=Applications(
            assistants=PaginatedPermissions[AssistantSparse](
                permissions=[ResourcePermission.READ, ResourcePermission.CREATE],
                items=[assistant],
            ),
            apps=PaginatedPermissions[AppSparse](
                permissions=[ResourcePermission.READ, ResourcePermission.CREATE],
                items=[],
            ),
            services=PaginatedPermissions[ServiceSparse](
                permissions=[ResourcePermission.READ, ResourcePermission.CREATE],
                items=[service],
            ),
        ),
        knowledge=Knowledge(
            groups=PaginatedPermissions[GroupSparse](
                permissions=[ResourcePermission.READ, ResourcePermission.CREATE],
                items=[TEST_GROUP],
            ),
            websites=PaginatedPermissions[WebsiteSparse](
                permissions=[ResourcePermission.READ, ResourcePermission.CREATE],
                items=[TEST_WEBSITE],
            ),
        ),
        members=PaginatedPermissions[SpaceMember](
            permissions=[
                ResourcePermission.READ,
                ResourcePermission.ADD,
                ResourcePermission.EDIT,
                ResourcePermission.REMOVE,
            ],
            items=[admin, editor],
        ),
        permissions=[
            ResourcePermission.READ,
            ResourcePermission.EDIT,
            ResourcePermission.DELETE,
        ],
    )

    space = MagicMock(
        created_at=now,
        updated_at=now,
        id=TEST_UUID,
        user_id=None,
        description=None,
        embedding_models=[embedding_model],
        completion_models=[completion_model],
        assistant=TEST_DEFAULT_ASSISTANT,
        assistants=[assistant],
        services=[service],
        websites=[TEST_WEBSITE],
        groups=[TEST_GROUP],
        tenant_id=tenant_id,
        members={admin.id: admin, editor.id: editor},
    )
    space.name = test_name
    space.is_personal.return_value = False

    space_assembler.user = MagicMock(id=admin.id)
    space_assembler.assistant_assembler.from_assistant_to_default_assistant_model.return_value = (
        TEST_DEFAULT_ASSISTANT
    )
    space_public = space_assembler.from_space_to_model(space)

    assert space_public == expected_space


def test_from_personal_space_to_model_sets_personal(
    space: Space, space_assembler: SpaceAssembler
):
    space.user_id = TEST_UUID

    space_public = space_assembler.from_space_to_model(space)

    assert space_public.personal


def test_space_members_ordering(space: Space, space_assembler: SpaceAssembler):
    admin = SpaceMember(
        id=TEST_UUID,
        email="admin@example.com",
        username="admin",
        role=SpaceRole.ADMIN,
    )
    editor = SpaceMember(
        id=uuid4(),
        email="editor@example.com",
        username="editor",
        role=SpaceRole.EDITOR,
    )
    editor_2 = SpaceMember(
        id=uuid4(),
        email="editor2@example.com",
        username="editor2",
        role=SpaceRole.EDITOR,
    )

    space.members = {admin.id: admin, editor.id: editor, editor_2.id: editor_2}

    space_assembler.user = MagicMock(id=editor_2.id)
    space_public = space_assembler.from_space_to_model(space)

    assert space_public.members.items == [editor_2, admin, editor]


def test_only_org_enabled_completion_models_are_returned(
    space: Space, space_assembler: SpaceAssembler
):
    space.completion_models = [TEST_MODEL_GPT4]

    space_public = space_assembler.from_space_to_model(space)

    assert space_public.completion_models == []


def test_only_org_enabled_embedding_models_are_returned(
    space: Space, space_assembler: SpaceAssembler
):
    space.embedding_models = [TEST_EMBEDDING_MODEL]

    space_public = space_assembler.from_space_to_model(space)

    assert space_public.embedding_models == []
