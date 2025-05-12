from typing import Optional
from uuid import UUID

from sqlalchemy import JSON, BigInteger, ForeignKey, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from intric.database.tables.ai_models_table import EmbeddingModels
from intric.database.tables.base_class import BasePublic
from intric.database.tables.spaces_table import Spaces
from intric.database.tables.tenant_table import Tenants
from intric.database.tables.users_table import Users


class Integration(BasePublic):
    __tablename__ = "integrations"

    name: Mapped[str] = mapped_column(Text, index=True, unique=True)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    integration_type: Mapped[str] = mapped_column(
        Text, index=True, server_default="default_type"
    )


class TenantIntegration(BasePublic):
    __tablename__ = "tenant_integrations"

    tenant_id: Mapped[UUID] = mapped_column(ForeignKey(Tenants.id, ondelete="CASCADE"))
    integration_id: Mapped[UUID] = mapped_column(
        ForeignKey(Integration.id, ondelete="CASCADE")
    )

    integration: Mapped[Integration] = relationship()

    __table_args__ = (
        UniqueConstraint(
            "tenant_id",
            "integration_id",
            name="tenant_integration_tenant_id_integration_id_unique",
        ),
    )


class UserIntegration(BasePublic):
    __tablename__ = "user_integrations"

    user_id: Mapped[UUID] = mapped_column(ForeignKey(Users.id, ondelete="CASCADE"))
    tenant_id: Mapped[UUID] = mapped_column(ForeignKey(Tenants.id, ondelete="CASCADE"))
    tenant_integration_id: Mapped[UUID] = mapped_column(
        ForeignKey(TenantIntegration.id, ondelete="CASCADE")
    )
    authenticated: Mapped[bool] = mapped_column(server_default="False", nullable=False)

    tenant_integration: Mapped[TenantIntegration] = relationship()

    __table_args__ = (
        UniqueConstraint(
            "user_id",
            "tenant_integration_id",
            name="user_integration_user_id_tenant_integration_id_unique",
        ),
    )


class OauthToken(BasePublic):
    __tablename__ = "oauth_tokens"

    access_token: Mapped[str] = mapped_column(Text)
    token_type: Mapped[str] = mapped_column(Text)
    refresh_token: Mapped[str] = mapped_column(Text)
    resources: Mapped[JSON] = mapped_column(JSONB)
    user_integration_id: Mapped[UUID] = mapped_column(
        ForeignKey(UserIntegration.id, ondelete="CASCADE")
    )

    user_integration: Mapped[UserIntegration] = relationship()


class IntegrationKnowledge(BasePublic):
    __tablename__ = "integration_knowledge"

    name: Mapped[Optional[str]] = mapped_column(Text)
    url: Mapped[Optional[str]] = mapped_column(Text)
    space_id: Mapped[UUID] = mapped_column(ForeignKey(Spaces.id, ondelete="CASCADE"))
    embedding_model_id: Mapped[UUID] = mapped_column(
        ForeignKey(EmbeddingModels.id, ondelete="CASCADE")
    )
    tenant_id: Mapped[UUID] = mapped_column(ForeignKey(Tenants.id, ondelete="CASCADE"))
    user_integration_id: Mapped[UUID] = mapped_column(
        ForeignKey(UserIntegration.id, ondelete="CASCADE")
    )
    size: Mapped[int] = mapped_column(BigInteger, nullable=True)

    user_integration: Mapped[UserIntegration] = relationship()
    embedding_model: Mapped[EmbeddingModels] = relationship()
