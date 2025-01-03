from datetime import datetime
from typing import Literal, Optional
from uuid import UUID

from pydantic import BaseModel, Field, computed_field


class TemplateWizard(BaseModel):
    required: bool = False
    title: Optional[str] = None
    description: Optional[str] = None


class AssistantTemplateWizard(BaseModel):
    attachments: Optional[TemplateWizard]
    collections: Optional[TemplateWizard]


class CompletionModelPublicAssistantTemplate(BaseModel):
    id: UUID


class PromptPublicAssistantTemplate(BaseModel):
    text: Optional[str]


class AssistantInTemplatePublic(BaseModel):
    name: str
    completion_model: Optional[CompletionModelPublicAssistantTemplate]
    completion_model_kwargs: dict = Field(default={})
    prompt: Optional[PromptPublicAssistantTemplate]


class AssistantTemplatePublic(BaseModel):
    id: UUID
    created_at: datetime
    updated_at: datetime
    name: str
    description: str
    category: str
    assistant: AssistantInTemplatePublic
    type: Literal["assistant"]
    wizard: AssistantTemplateWizard


class AssistantTemplateListPublic(BaseModel):
    items: list[AssistantTemplatePublic]

    @computed_field(description="Number of items returned in the response")
    @property
    def count(self) -> int:
        return len(self.items)
