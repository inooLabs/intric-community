from datetime import datetime
from uuid import UUID

from fastapi import APIRouter, Depends, Query

from intric.assistants.api import assistant_protocol
from intric.assistants.api.assistant_models import (
    AskAssistant,
    AssistantCreatePublic,
    AssistantPublic,
    AssistantUpdatePublic,
)
from intric.authentication.auth_models import ApiKey
from intric.database.database import AsyncSession, get_session_with_transaction
from intric.main.config import SETTINGS
from intric.main.container.container import Container
from intric.main.models import CursorPaginatedResponse, PaginatedResponse
from intric.prompts.api.prompt_models import PromptSparse
from intric.server import protocol
from intric.server.dependencies.container import get_container
from intric.server.protocol import responses
from intric.sessions.session import (
    AskResponse,
    SessionFeedback,
    SessionMetadataPublic,
    SessionPublic,
)
from intric.sessions.session_protocol import (
    to_session_public,
    to_sessions_paginated_response,
)
from intric.spaces.api.space_models import TransferApplicationRequest

router = APIRouter()


@router.post(
    "/",
    response_model=AssistantPublic,
    responses=responses.get_responses([404]),
    deprecated=True,
)
async def create_assistant(
    assistant: AssistantCreatePublic,
    container: Container = Depends(get_container(with_user=True)),
):

    service = container.assistant_service()
    assembler = container.assistant_assembler()

    assistant, permissions = await service.create_assistant(
        name=assistant.name,
        prompt=assistant.prompt,
        space_id=assistant.space_id,
        completion_model_kwargs=assistant.completion_model_kwargs,
        logging_enabled=assistant.logging_enabled,
        groups=[group.id for group in assistant.groups],
        websites=[website.id for website in assistant.websites],
        completion_model_id=assistant.completion_model.id,
    )

    return assembler.from_assistant_to_model(assistant, permissions=permissions)


@router.get("/", response_model=PaginatedResponse[AssistantPublic])
async def get_assistants(
    name: str = None,
    for_tenant: bool = False,
    container: Container = Depends(get_container(with_user=True)),
):
    """Requires Admin permission if `for_tenant` is `true`."""
    service = container.assistant_service()
    assembler = container.assistant_assembler()

    assistants = await service.get_assistants(name, for_tenant)

    assistants = [
        assembler.from_assistant_to_model(assistant) for assistant in assistants
    ]

    return protocol.to_paginated_response(assistants)


@router.get(
    "/{id}/",
    response_model=AssistantPublic,
    responses=responses.get_responses([400, 404]),
)
async def get_assistant(
    id: UUID,
    container: Container = Depends(get_container(with_user=True)),
):
    service = container.assistant_service()
    assembler = container.assistant_assembler()

    assistant, permissions = await service.get_assistant(assistant_id=id)

    return assembler.from_assistant_to_model(
        assistant=assistant, permissions=permissions
    )


@router.post(
    "/{id}/",
    response_model=AssistantPublic,
    responses=responses.get_responses([400, 404]),
)
async def update_assistant(
    id: UUID,
    assistant: AssistantUpdatePublic,
    container: Container = Depends(get_container(with_user=True)),
):
    """Omitted fields are not updated"""
    service = container.assistant_service()
    assembler = container.assistant_assembler()

    attachment_ids = None
    if assistant.attachments is not None:
        attachment_ids = [attachment.id for attachment in assistant.attachments]

    groups = None
    if assistant.groups is not None:
        groups = [group.id for group in assistant.groups]

    websites = None
    if assistant.websites is not None:
        websites = [website.id for website in assistant.websites]

    completion_model_id = None
    if assistant.completion_model is not None:
        completion_model_id = assistant.completion_model.id

    completion_model_kwargs = None
    if assistant.completion_model_kwargs is not None:
        completion_model_kwargs = assistant.completion_model_kwargs

    assistant, permissions = await service.update_assistant(
        assistant_id=id,
        name=assistant.name,
        prompt=assistant.prompt,
        completion_model_id=completion_model_id,
        completion_model_kwargs=completion_model_kwargs,
        logging_enabled=assistant.logging_enabled,
        attachment_ids=attachment_ids,
        groups=groups,
        websites=websites,
    )

    return assembler.from_assistant_to_model(assistant, permissions=permissions)


@router.delete(
    "/{id}/",
    status_code=204,
    responses=responses.get_responses([403, 404]),
)
async def delete_assistant(
    id: UUID,
    container: Container = Depends(get_container(with_user=True)),
):
    service = container.assistant_service()
    await service.delete_assistant(id)


@router.post(
    "/{id}/sessions/",
    response_model=AskResponse,
    responses=responses.streaming_response(AskResponse, [400, 404]),
)
async def ask_assistant(
    id: UUID,
    ask: AskAssistant,
    version: int = Query(default=1, ge=1, le=2),
    container: Container = Depends(
        get_container(with_user_from_assistant_api_key=True)
    ),
    db_session: AsyncSession = Depends(get_session_with_transaction),
):
    """Streams the response as Server-Sent Events if stream == true"""
    service = container.assistant_service()

    file_ids = [file.id for file in ask.files]
    tool_assistant_id = ask.tools.assistants[0].id if ask.tools is not None else None
    response = await service.ask(
        question=ask.question,
        assistant_id=id,
        file_ids=file_ids,
        stream=ask.stream,
        tool_assistant_id=tool_assistant_id,
        version=version,
    )

    return await assistant_protocol.to_response(
        response=response, db_session=db_session, stream=ask.stream
    )


@router.get(
    "/{id}/sessions/",
    response_model=CursorPaginatedResponse[SessionMetadataPublic],
    responses=responses.get_responses([400, 404]),
)
async def get_assistant_sessions(
    id: UUID,
    limit: int = Query(default=None, gt=0),
    cursor: datetime = None,
    previous: bool = False,
    container: Container = Depends(get_container(with_user=True)),
):
    assistant_service = container.assistant_service()
    session_service = container.session_service()

    assistant_in_db, _ = await assistant_service.get_assistant(id)

    sessions, total_count = await session_service.get_sessions_by_assistant(
        assistant_id=assistant_in_db.id,
        limit=limit,
        cursor=cursor,
        previous=previous,
    )
    return to_sessions_paginated_response(
        sessions=sessions,
        limit=limit,
        cursor=cursor,
        previous=previous,
        total_count=total_count,
    )


@router.get(
    "/{id}/sessions/{session_id}/",
    response_model=SessionPublic,
    responses=responses.get_responses([400, 404]),
)
async def get_assistant_session(
    id: UUID,
    session_id: UUID,
    container: Container = Depends(get_container(with_user=True)),
):
    session_service = container.session_service()
    session = await session_service.get_session_by_uuid(session_id, assistant_id=id)

    return to_session_public(session)


@router.delete(
    "/{id}/sessions/{session_id}/",
    response_model=SessionPublic,
    responses=responses.get_responses([400, 404]),
)
async def delete_assistant_session(
    id: UUID,
    session_id: UUID,
    container: Container = Depends(get_container(with_user=True)),
):
    session_service = container.session_service()
    session = await session_service.delete(session_id, assistant_id=id)

    return to_session_public(session)


@router.post(
    "/{id}/sessions/{session_id}/",
    response_model=AskResponse,
    responses=responses.streaming_response(AskResponse, [400, 404]),
)
async def ask_followup(
    id: UUID,
    session_id: UUID,
    ask: AskAssistant,
    version: int = Query(default=1, ge=1, le=2),
    container: Container = Depends(
        get_container(with_user_from_assistant_api_key=True)
    ),
    db_session: AsyncSession = Depends(get_session_with_transaction),
):
    """Streams the response as Server-Sent Events if stream == true"""
    service = container.assistant_service()

    file_ids = [file.id for file in ask.files]
    tool_assistant_id = ask.tools.assistants[0].id if ask.tools is not None else None
    response = await service.ask(
        question=ask.question,
        assistant_id=id,
        file_ids=file_ids,
        stream=ask.stream,
        session_id=session_id,
        tool_assistant_id=tool_assistant_id,
        version=version,
    )

    return await assistant_protocol.to_response(
        response=response, db_session=db_session, stream=ask.stream
    )


@router.post(
    "/{id}/sessions/{session_id}/feedback/",
    response_model=SessionPublic,
    responses=responses.get_responses([400, 404]),
)
async def leave_feedback(
    id: UUID,
    session_id: UUID,
    feedback: SessionFeedback,
    container: Container = Depends(
        get_container(with_user_from_assistant_api_key=True)
    ),
):
    session_service = container.session_service()
    session = await session_service.leave_feedback(
        session_id=session_id, assistant_id=id, feedback=feedback
    )

    return to_session_public(session)


@router.get("/{id}/api-keys/", response_model=ApiKey)
async def generate_read_only_assistant_key(
    id: UUID,
    container: Container = Depends(get_container(with_user=True)),
):
    """Generates a read-only api key for this assistant.

    This api key can only be used on `POST /api/v1/assistants/{id}/sessions/`
    and `POST /api/v1/assistants/{id}/sessions/{session_id}/`."""
    service = container.assistant_service()
    return await service.generate_api_key(id)


@router.post("/{id}/transfer/", status_code=204)
async def transfer_assistant_to_space(
    id: UUID,
    transfer_req: TransferApplicationRequest,
    container: Container = Depends(get_container(with_user=True)),
):
    service = container.assistant_service()
    await service.move_assistant_to_space(
        assistant_id=id,
        space_id=transfer_req.target_space_id,
        move_resources=transfer_req.move_resources,
    )


@router.get(
    "/{id}/prompts/",
    response_model=PaginatedResponse[PromptSparse],
    include_in_schema=SETTINGS.dev,
)
async def get_prompts(
    id: UUID, container: Container = Depends(get_container(with_user=True))
):
    service = container.assistant_service()
    assembler = container.prompt_assembler()

    prompts = await service.get_prompts_by_assistant(id)
    prompts = [assembler.from_prompt_to_model(prompt) for prompt in prompts]

    return protocol.to_paginated_response(prompts)


if SETTINGS.using_intric_proprietary:
    from intric_prop.assistants.api.assistant_router_prop import include_prop_endpoints

    include_prop_endpoints(router=router)
