from enum import Enum
from typing import Optional
from uuid import UUID

from pydantic import BaseModel

from intric.ai_models.completion_models.completion_model import (
    ModelHostingLocation,
    ModelStability,
    Orgs,
)
from intric.main.models import InDB, partial_model
from intric.securitylevels.api.security_level_models import SecurityLevelPublic


class EmbeddingModelFamily(str, Enum):
    OPEN_AI = "openai"
    MINI_LM = "mini_lm"
    E5 = "e5"


class EmbeddingModelBase(BaseModel):
    name: str
    family: EmbeddingModelFamily
    is_deprecated: bool
    open_source: bool
    dimensions: Optional[int] = None
    max_input: Optional[int] = None
    hf_link: Optional[str] = None
    stability: ModelStability
    hosting: ModelHostingLocation
    description: Optional[str] = None
    org: Optional[Orgs] = None


class EmbeddingModelCreate(EmbeddingModelBase):
    pass


@partial_model
class EmbeddingModelUpdate(EmbeddingModelBase):
    id: UUID


class EmbeddingModelUpdateFlags(BaseModel):
    is_org_enabled: Optional[bool] = False
    security_level_id: Optional[UUID] = None


class EmbeddingModelSecurityLevelUpdate(BaseModel):
    security_level_id: UUID


class EmbeddingModel(EmbeddingModelBase, InDB):
    is_org_enabled: bool = False
    security_level_id: Optional[UUID] = None

class EmbeddingModelPublicBase(EmbeddingModelBase, InDB):
    pass


class EmbeddingModelPublic(EmbeddingModel):
    can_access: bool = False
    is_locked: bool = True
    security_level: Optional[SecurityLevelPublic] = None


class EmbeddingModelSparse(EmbeddingModelBase, InDB):
    pass
