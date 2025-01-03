from enum import Enum
from typing import Literal, Optional
from uuid import UUID

from pydantic import BaseModel

from intric.ai_models.completion_models.completion_model import (
    CompletionModelSparse,
    ModelKwargs,
)
from intric.ai_models.embedding_models.embedding_model import EmbeddingModelSparse
from intric.assistants.api.assistant_models import AssistantSparse, DefaultAssistant
from intric.groups.group import GroupMetadata, GroupSparse
from intric.main.models import (
    InDB,
    ModelId,
    PaginatedPermissions,
    ResourcePermissionsMixin,
    partial_model,
)
from intric.services.service import ServiceSparse
from intric.users.user import UserSparse
from intric.websites.crawl_dependencies.crawl_models import CrawlRunPublic, CrawlType
from intric.websites.website_models import UpdateInterval, WebsiteSparse


class SpaceRole(str, Enum):
    ADMIN = "admin"
    EDITOR = "editor"
    VIEWER = "viewer"


class CreateRequest(BaseModel):
    name: str


class TransferRequest(BaseModel):
    target_space_id: UUID


class TransferApplicationRequest(TransferRequest):
    move_resources: bool = False


# Members


class SpaceMember(UserSparse):
    role: SpaceRole


# Apps


class AppSparse(ResourcePermissionsMixin, InDB):
    name: str
    description: Optional[str] = None
    published: bool

    user_id: UUID


# Spaces


class CreateSpaceRequest(CreateRequest):
    pass


@partial_model
class UpdateSpaceRequest(BaseModel):
    name: str
    description: str

    embedding_models: list[ModelId]
    completion_models: list[ModelId]


class Applications(BaseModel):
    assistants: PaginatedPermissions[AssistantSparse]
    services: PaginatedPermissions[ServiceSparse]
    apps: PaginatedPermissions[AppSparse]


class Knowledge(BaseModel):
    groups: PaginatedPermissions[GroupSparse]
    websites: PaginatedPermissions[WebsiteSparse]


class SpaceSparse(InDB, ResourcePermissionsMixin):
    name: str
    description: Optional[str]
    personal: bool


class SpaceDashboard(SpaceSparse):
    applications: Applications


class SpacePublic(SpaceDashboard):
    embedding_models: list[EmbeddingModelSparse]

    completion_models: list[CompletionModelSparse]
    knowledge: Knowledge
    members: PaginatedPermissions[SpaceMember]

    default_assistant: DefaultAssistant


# Assistants


class WizardType(str, Enum):
    attachments = "attachments"
    groups = "groups"


class AdditionalField(BaseModel):
    type: WizardType
    value: list[dict[str, UUID]]


class TemplateCreate(BaseModel):
    id: UUID
    additional_fields: Optional[list[AdditionalField]]

    def get_ids_by_type(self, wizard_type: WizardType) -> list[UUID]:
        if self.additional_fields is None:
            return []

        return [
            item["id"]
            for field in self.additional_fields
            if field.type == wizard_type
            for item in field.value
        ]


class CreateSpaceAssistantRequest(CreateRequest):
    from_template: Optional[TemplateCreate] = None


class CreateSpaceAppRequest(CreateRequest):
    from_template: Optional[TemplateCreate] = None


class CreateSpaceServiceRequest(CreateRequest):
    pass


class CreateSpaceServiceResponse(InDB):
    name: str
    prompt: str
    completion_model_kwargs: ModelKwargs
    output_format: Optional[Literal["json", "list", "boolean"]] = None
    json_schema: Optional[dict] = None

    groups: list[GroupSparse]
    completion_model: Optional[CompletionModelSparse]
    published: bool = False
    user: UserSparse


# Groups


class CreateSpaceGroupsRequest(CreateRequest):
    embedding_model: Optional[ModelId] = None


class CreateSpaceGroupsResponse(InDB):
    name: str
    embedding_model: Optional[EmbeddingModelSparse]
    user: UserSparse
    metadata: GroupMetadata
    published: bool


# Websites


class CreateSpaceWebsitesRequest(BaseModel):
    name: Optional[str] = None
    url: str
    download_files: bool = False
    crawl_type: CrawlType = CrawlType.CRAWL
    update_interval: UpdateInterval = UpdateInterval.NEVER
    embedding_model: Optional[ModelId] = None


class CreateSpaceWebsitesResponse(InDB):
    name: Optional[str] = None
    url: str

    download_files: bool
    crawl_type: CrawlType
    update_interval: UpdateInterval

    embedding_model: Optional[EmbeddingModelSparse]
    latest_crawl: Optional[CrawlRunPublic]
    published: bool


# Members


class AddSpaceMemberRequest(BaseModel):
    id: UUID
    role: SpaceRole


class UpdateSpaceMemberRequest(BaseModel):
    role: SpaceRole
