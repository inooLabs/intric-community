# MIT License

from uuid import UUID

from fastapi import APIRouter, Depends

from intric.ai_models.completion_models.completion_model import (
    CompletionModelPublic,
    CompletionModelUpdateFlags,
)
from intric.main.container.container import Container
from intric.main.models import PaginatedResponse
from intric.server import protocol
from intric.server.dependencies.container import get_container
from intric.server.protocol import responses

router = APIRouter()


@router.get(
    "/",
    response_model=PaginatedResponse[CompletionModelPublic],
)
async def get_completion_models(
    container: Container = Depends(get_container(with_user=True)),
):
    service = container.ai_models_service()

    models = await service.get_completion_models()

    return protocol.to_paginated_response(models)


@router.post(
    "/{id}/",
    response_model=CompletionModelPublic,
    responses=responses.get_responses([404]),
)
async def enable_completion_model(
    id: UUID,
    data: CompletionModelUpdateFlags,
    container: Container = Depends(get_container(with_user=True)),
):
    service = container.ai_models_service()
    return await service.enable_completion_model(completion_model_id=id, data=data)
