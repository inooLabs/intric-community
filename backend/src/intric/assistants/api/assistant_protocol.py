import re
from typing import TYPE_CHECKING, Optional

from sse_starlette import EventSourceResponse

from intric.ai_models.completion_models.completion_model import CompletionModel
from intric.database.database import AsyncSession
from intric.database.transaction import gen_transaction
from intric.files.file_models import File, FilePublic
from intric.info_blobs.info_blob import (
    InfoBlobAskAssistantPublic,
    InfoBlobInDB,
    InfoBlobMetadata,
)
from intric.main.logging import get_logger
from intric.questions.question import UseTools
from intric.sessions.session import AskResponse, SessionInDB

if TYPE_CHECKING:
    from intric.assistants.api.assistant_models import AssistantResponse
    from intric.info_blobs.info_blob import InfoBlobInDBWithScore

logger = get_logger(__name__)

REFERENCE_PATTERN = r'<intric-info-blob id="([0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12})"/>'  # noqa


def _get_references(response_string: str, info_blobs: list["InfoBlobInDBWithScore"]):
    info_blob_ids = re.findall(REFERENCE_PATTERN, response_string)

    return [blob for blob in info_blobs if str(blob.id) in info_blob_ids]


def to_ask_response(
    question: str,
    files: list[File],
    session: SessionInDB,
    answer: str,
    info_blobs: list[InfoBlobInDB],
    completion_model: Optional[CompletionModel] = None,
    tools: "UseTools" = None,
):
    return AskResponse(
        question=question,
        files=[FilePublic(**file.model_dump()) for file in files],
        session_id=session.id,
        answer=answer,
        references=[
            InfoBlobAskAssistantPublic(
                **blob.model_dump(),
                metadata=InfoBlobMetadata(**blob.model_dump()),
            )
            for blob in info_blobs
        ],
        model=completion_model,
        tools=tools,
    )


async def to_response(
    response: "AssistantResponse",
    db_session: AsyncSession,
    stream: bool,
    version: int = 1,
):
    if stream:

        @gen_transaction(db_session)
        async def event_stream():
            async for response_string, chunk in response.answer:
                if version == 1:
                    references = response.info_blobs
                elif version == 2:
                    references = _get_references(
                        response_string=response_string, info_blobs=response.info_blobs
                    )

                yield to_ask_response(
                    question=response.question,
                    files=response.files,
                    session=response.session,
                    answer=chunk,
                    info_blobs=references,
                    completion_model=response.completion_model,
                    tools=response.tools,
                ).model_dump_json()

        return EventSourceResponse(event_stream())

    if version == 1:
        references = response.info_blobs
    elif version == 2:
        references = _get_references(
            response_string=response.answer, info_blobs=response.info_blobs
        )

    return to_ask_response(
        question=response.question,
        files=response.files,
        session=response.session,
        answer=response.answer,
        info_blobs=references,
        completion_model=response.completion_model,
        tools=response.tools,
    )
