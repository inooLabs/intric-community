from typing import Optional
from uuid import UUID

from sqlalchemy import ForeignKey
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from intric.database.tables.ai_models_table import CompletionModels
from intric.database.tables.base_class import BasePublic


class AppTemplates(BasePublic):
    name: Mapped[str] = mapped_column()
    description: Mapped[Optional[str]] = mapped_column()
    category: Mapped[str] = mapped_column()
    prompt_text: Mapped[Optional[str]] = mapped_column()
    input_description: Mapped[Optional[str]] = mapped_column()
    input_type: Mapped[str] = mapped_column()
    completion_model_kwargs: Mapped[Optional[dict]] = mapped_column(JSONB)
    wizard: Mapped[Optional[dict]] = mapped_column(JSONB)

    completion_model_id: Mapped[Optional[UUID]] = mapped_column(
        ForeignKey(CompletionModels.id),
    )

    completion_model: Mapped[CompletionModels] = relationship()
