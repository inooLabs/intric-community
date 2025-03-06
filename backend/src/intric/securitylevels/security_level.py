# Copyright (c) 2025 Sundsvalls Kommun
#
# Licensed under the MIT License.

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class SecurityLevelBase(BaseModel):
    """Base model for security levels."""
    name: str
    description: str | None = None
    value: int = 0


class SecurityLevelCreate(SecurityLevelBase):
    """Model for creating a security level."""
    tenant_id: UUID
    model_config = ConfigDict(from_attributes=True)


class SecurityLevelUpdate(SecurityLevelBase):
    """Model for updating a security level."""
    id: UUID
    tenant_id: UUID
    name: str | None = None
    description: str | None = None
    value: int | None = None
    model_config = ConfigDict(from_attributes=True)


class SecurityLevel(SecurityLevelBase):
    """Domain model for security levels."""
    id: UUID | None = None
    tenant_id: UUID
    created_at: datetime | None = None
    updated_at: datetime | None = None
    deleted_at: datetime | None = None
    model_config = ConfigDict(from_attributes=True)
