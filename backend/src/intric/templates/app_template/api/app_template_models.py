from datetime import datetime
from typing import Literal, Optional
from uuid import UUID

from pydantic import BaseModel, computed_field


class TemplateWizard(BaseModel):
    required: bool = False
    title: Optional[str] = None
    description: Optional[str] = None


class AppTemplateWizard(BaseModel):
    attachments: Optional[TemplateWizard]
    collections: Optional[TemplateWizard]


class CompletionModelPublicAppTemplate(BaseModel):
    id: UUID


class PromptPublicAppTemplate(BaseModel):
    text: Optional[str]


class AppInTemplatePublic(BaseModel):
    name: str
    completion_model: Optional[CompletionModelPublicAppTemplate]
    completion_model_kwargs: dict
    prompt: Optional[PromptPublicAppTemplate]
    input_description: Optional[str]
    input_type: str


class AppTemplatePublic(BaseModel):
    id: UUID
    created_at: datetime
    updated_at: datetime
    name: str
    description: Optional[str]
    category: str
    app: AppInTemplatePublic
    type: Literal["app"]
    wizard: AppTemplateWizard


class AppTemplateListPublic(BaseModel):
    items: list[AppTemplatePublic]

    @computed_field(description="Number of items returned in the response")
    @property
    def count(self) -> int:
        return len(self.items)
