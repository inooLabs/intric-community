from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from uuid import UUID

    from intric.integration.domain.entities.integration import Integration


class IntegrationRepository(ABC):
    @abstractmethod
    async def all(self) -> list["Integration"]: ...

    @abstractmethod
    async def one_or_none(
        self, id: "UUID | None" = None, **filters
    ) -> "Integration | None": ...

    @abstractmethod
    async def one(self, id: "UUID | None" = None, **filters) -> "Integration": ...

    @abstractmethod
    async def add(self, obj: "Integration") -> "Integration": ...
