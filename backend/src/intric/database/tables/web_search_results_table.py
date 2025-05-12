from uuid import UUID

from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column

from intric.database.tables.base_class import BasePublic
from intric.database.tables.questions_table import Questions


class WebSearchResult(BasePublic):
    __tablename__ = "web_search_results"

    title: Mapped[str] = mapped_column()
    content: Mapped[str] = mapped_column()
    url: Mapped[str] = mapped_column()
    score: Mapped[float] = mapped_column()

    # Foreign keys
    question_id: Mapped[UUID] = mapped_column(
        ForeignKey(Questions.id, ondelete="CASCADE")
    )
