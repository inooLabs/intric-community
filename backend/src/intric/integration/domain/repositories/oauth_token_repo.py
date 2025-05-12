from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from uuid import UUID

    from intric.integration.domain.entities.oauth_token import OauthToken


class OauthTokenRepository(ABC):
    @abstractmethod
    async def one_or_none(
        self, id: "UUID | None" = None, **filters
    ) -> "OauthToken | None": ...

    @abstractmethod
    async def one(self, id: "UUID | None" = None, **filters) -> "OauthToken": ...

    @abstractmethod
    async def add(self, obj: "OauthToken") -> "OauthToken": ...

    @abstractmethod
    async def update(self, obj: "OauthToken") -> "OauthToken": ...
