from uuid import UUID

from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column

from intric.database.tables.base_class import BasePublic
from intric.database.tables.tenant_table import Tenants


class AllowedOrigins(BasePublic):
    url: Mapped[str] = mapped_column(index=True, unique=True)
    tenant_id: Mapped[UUID] = mapped_column(ForeignKey(Tenants.id, ondelete="CASCADE"))
