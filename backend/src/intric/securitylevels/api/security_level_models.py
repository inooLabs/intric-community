# Copyright (c) 2025 Sundsvalls Kommun
#
# Licensed under the MIT License.

from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field

from intric.main.models import InDB, partial_model


class SecurityLevelBase(BaseModel):
    """Base model for security level data."""

    name: str = Field(..., description="Name of the security level")
    description: Optional[str] = Field(
        None, description="Description of the security level"
    )
    value: int = Field(
        ..., description="Numeric value determining the security level hierarchy"
    )


class SecurityLevelCreatePublic(SecurityLevelBase):
    """Request model for creating a new security level."""
    pass


@partial_model
class SecurityLevelUpdatePublic(SecurityLevelCreatePublic):
    """Request model for updating an existing security level."""


class SecurityLevelSparse(InDB):
    """Basic security level information."""
    name: str
    description: Optional[str]
    value: int


class SecurityLevelPublic(SecurityLevelSparse):
    """Complete security level information including relationships."""
    pass
