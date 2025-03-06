# Copyright (c) 2025 Sundsvalls Kommun
#
# Licensed under the MIT License.

from uuid import UUID

from fastapi import APIRouter, Depends

from intric.securitylevels.security_level_factory import get_security_level_service
from intric.securitylevels.security_level_service import SecurityLevelService
from intric.server.protocol import responses
from intric.securitylevels.api.security_level_models import (
    SecurityLevelCreatePublic,
    SecurityLevelPublic,
    SecurityLevelUpdatePublic,
)

router = APIRouter()


@router.post(
    "",
    response_model=SecurityLevelPublic,
    status_code=201,
    responses=responses.get_responses([400, 409]),
)
async def create_security_level(
    request: SecurityLevelCreatePublic,
    service: SecurityLevelService = Depends(get_security_level_service),
) -> SecurityLevelPublic:
    """Create a new security level for the current tenant.

    Args:
        request: The security level creation request.

    Returns:
        The created security level.

    Raises:
        400: If the request is invalid.
        409: If a security level with the same name already exists for this tenant.
    """
    security_level = await service.create_security_level(
        name=request.name,
        description=request.description,
        value=request.value,
    )
    return SecurityLevelPublic.model_validate(security_level)


@router.get(
    "",
    response_model=list[SecurityLevelPublic],
    responses=responses.get_responses([403]),
)
async def list_security_levels(
    service: SecurityLevelService = Depends(get_security_level_service),
) -> list[SecurityLevelPublic]:
    """List all security levels for the current tenant ordered by value.

    Returns:
        List of security levels ordered by value.

    Raises:
        403: If the user doesn't have permission to list security levels.
    """
    security_levels = await service.list_security_levels()
    return [SecurityLevelPublic.model_validate(sl) for sl in security_levels]


@router.get(
    "/{id}",
    response_model=SecurityLevelPublic,
    responses=responses.get_responses([403, 404]),
)
async def get_security_level(
    id: UUID,
    service: SecurityLevelService = Depends(get_security_level_service),
) -> SecurityLevelPublic:
    """Get a security level by ID.

    Args:
        id: The ID of the security level.

    Returns:
        The security level.

    Raises:
        403: If the user doesn't have permission to view the security level.
        404: If the security level doesn't exist or belongs to a different tenant.
    """
    security_level = await service.get_security_level(id)
    return SecurityLevelPublic.model_validate(security_level)


@router.patch(
    "/{id}",
    response_model=SecurityLevelPublic,
    responses=responses.get_responses([400, 403, 404, 409]),
)
async def update_security_level(
    id: UUID,
    request: SecurityLevelUpdatePublic,
    service: SecurityLevelService = Depends(get_security_level_service),
) -> SecurityLevelPublic:
    """Update a security level.

    Args:
        id: The ID of the security level to update.
        request: The update request.

    Returns:
        The updated security level.

    Raises:
        400: If the request is invalid.
        403: If the user doesn't have permission to update the security level.
        404: If the security level doesn't exist or belongs to a different tenant.
        409: If updating the name would create a duplicate within the tenant.
    """
    security_level = await service.update_security_level(
        id=id,
        name=request.name,
        description=request.description,
        value=request.value,
    )
    return SecurityLevelPublic.model_validate(security_level)


@router.delete(
    "/{id}",
    status_code=204,
    responses=responses.get_responses([403, 404, 409]),
)
async def delete_security_level(
    id: UUID,
    service: SecurityLevelService = Depends(get_security_level_service),
) -> None:
    """Delete a security level.

    Args:
        id: The ID of the security level to delete.

    Raises:
        403: If the user doesn't have permission to delete the security level.
        404: If the security level doesn't exist or belongs to a different tenant.
        409: If the security level is in use by any spaces or models.
    """
    await service.delete_security_level(id)
