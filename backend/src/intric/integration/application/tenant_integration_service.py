from typing import TYPE_CHECKING

from intric.integration.domain.entities.tenant_integration import TenantIntegration
from intric.main.exceptions import BadRequestException, UnauthorizedException
from intric.integration.presentation.models import TenantIntegrationFilter

if TYPE_CHECKING:
    from uuid import UUID

    from intric.integration.domain.repositories.integration_repo import (
        IntegrationRepository,
    )
    from intric.integration.domain.repositories.tenant_integration_repo import (
        TenantIntegrationRepository,
    )
    from intric.users.user import UserInDB


class TenantIntegrationService:
    def __init__(
        self,
        tenant_integration_repo: "TenantIntegrationRepository",
        integration_repo: "IntegrationRepository",
        user: "UserInDB",
    ):
        self.tenant_integration_repo = tenant_integration_repo
        self.integration_repo = integration_repo
        self.user = user

    async def get_tenant_integrations(
        self, filter: TenantIntegrationFilter
    ) -> list["TenantIntegration"]:
        tenant_integrations = await self.tenant_integration_repo.query(
            tenant_id=self.user.tenant_id
        )
        if filter == TenantIntegrationFilter.TENANT_ONLY:
            return tenant_integrations
        enabled_integration_id = [i.integration.id for i in tenant_integrations]
        global_integrations = await self.integration_repo.all()

        for item in global_integrations:
            if item.id in enabled_integration_id:
                continue
            # NOTE: Creating entity in application layer
            tenant_integrations.append(
                TenantIntegration(tenant_id=self.user.tenant_id, integration=item)
            )
        return tenant_integrations

    async def create_tenant_integration(
        self,
        integration_id: "UUID",
    ) -> "TenantIntegration":
        integration = await self.integration_repo.one(id=integration_id)
        result = await self.tenant_integration_repo.one_or_none(
            tenant_id=self.user.tenant_id, integration_id=integration.id
        )
        if result:
            raise BadRequestException("Integration existed for tenant")

        obj = TenantIntegration(integration=integration, tenant_id=self.user.tenant_id)
        tenant_integration = await self.tenant_integration_repo.add(obj=obj)
        return tenant_integration

    async def remove_tenant_integration(
        self,
        tenant_integration_id: "UUID",
    ) -> None:
        tenant_integration = await self.tenant_integration_repo.one(
            id=tenant_integration_id
        )
        if self.user.tenant_id != tenant_integration.tenant_id:
            raise UnauthorizedException()
        await self.tenant_integration_repo.delete(id=tenant_integration.id)
