# Copyright (c) 2025 Sundsvalls Kommun
#
# Licensed under the MIT License.

from typing import Optional
from uuid import UUID

from intric.main.exceptions import BadRequestException, NotFoundException, UnauthorizedException
from intric.roles.permissions import Permission, validate_permissions
from intric.securitylevels.security_level import SecurityLevel, SecurityLevelCreate, SecurityLevelUpdate
from intric.securitylevels.security_level_repo import SecurityLevelRepository
from intric.users.user import UserInDB


class SecurityLevelService:
    """Service for managing security levels."""

    def __init__(
        self,
        user: UserInDB,
        repo: SecurityLevelRepository,
    ):
        self.user = user
        self.repo = repo

    def _validate(self, security_level: SecurityLevel, id: UUID):
        """Validate security level exists and belongs to user's tenant."""
        if security_level is None or security_level.tenant_id != self.user.tenant_id:
            raise NotFoundException(f"Security level {id} not found")

    @validate_permissions(Permission.ADMIN)
    async def create_security_level(
        self, name: str, description: Optional[str], value: int
    ) -> SecurityLevel:
        """Create a new security level."""
        # Check if name already exists for this tenant
        existing = await self.repo.get_by_name_and_tenant(name, self.user.tenant_id)
        if existing:
            raise BadRequestException(f"Security level with name '{name}' already exists")

        security_level = SecurityLevelCreate(
            name=name,
            description=description,
            value=value,
            tenant_id=self.user.tenant_id,
        )

        return await self.repo.create(security_level)

    async def get_security_level(self, id: UUID) -> SecurityLevel:
        """Get a security level by ID."""
        security_level = await self.repo.get(id)
        self._validate(security_level, id)
        return security_level

    async def get_security_level_by_name(self, name: str) -> Optional[SecurityLevel]:
        """Get a security level by name for the current tenant."""
        return await self.repo.get_by_name_and_tenant(name, self.user.tenant_id)

    async def list_security_levels(self) -> list[SecurityLevel]:
        """List all security levels for the current tenant ordered by value."""
        return await self.repo.list_by_tenant(self.user.tenant_id)

    @validate_permissions(Permission.ADMIN)
    async def update_security_level(
        self,
        id: UUID,
        name: Optional[str] = None,
        description: Optional[str] = None,
        value: Optional[int] = None,
    ) -> SecurityLevel:
        """Update a security level."""
        security_level = await self.repo.get(id)
        self._validate(security_level, id)

        # Check if name already exists if updating name
        if name:
            existing = await self.repo.get_by_name_and_tenant(name, self.user.tenant_id)
            if existing and existing.id != id:
                raise BadRequestException(f"Security level with name '{name}' already exists")

        # Create update model
        update = SecurityLevelUpdate(
            id=id,
            tenant_id=self.user.tenant_id,
            name=name if name is not None else security_level.name,
            description=description if description is not None else security_level.description,
            value=value if value is not None else security_level.value,
        )

        return await self.repo.update(update)

    @validate_permissions(Permission.ADMIN)
    async def delete_security_level(self, id: UUID) -> None:
        """Delete a security level."""
        security_level = await self.repo.get(id)
        self._validate(security_level, id)
        await self.repo.delete(security_level.id)

    async def validate_security_level(
        self, required_level: SecurityLevel, provided_level: SecurityLevel
    ) -> bool:
        """Validate if a provided security level meets the required level."""
        # Ensure levels are from same tenant
        if required_level.tenant_id != provided_level.tenant_id:
            return False
        return provided_level.value >= required_level.value

    async def get_highest_security_level(self) -> Optional[int]:
        """Get the highest security level value for the current tenant."""
        return await self.repo.get_highest_value_by_tenant(self.user.tenant_id)
