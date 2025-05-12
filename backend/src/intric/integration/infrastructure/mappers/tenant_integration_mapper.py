from typing import Any, Dict, List

from intric.base.base_entity import EntityMapper
from intric.database.tables.integration_table import (
    TenantIntegration as TenantIntegrationDBModel,
)
from intric.integration.domain.entities.tenant_integration import TenantIntegration
from intric.integration.domain.factories.tenant_integration_factory import (
    TenantIntegrationFactory,
)


class TenantIntegrationMapper(
    EntityMapper[TenantIntegration, TenantIntegrationDBModel]
):
    def to_db_dict(self, entity: TenantIntegration) -> Dict[str, Any]:
        return {
            "tenant_id": entity.tenant_id,
            "integration_id": entity.integration.id,
        }

    def to_entity(self, db_model: TenantIntegrationDBModel) -> TenantIntegration:
        return TenantIntegrationFactory.create_entity(record=db_model)

    def to_entities(
        self, db_models: List[TenantIntegrationDBModel]
    ) -> List[TenantIntegration]:
        return TenantIntegrationFactory.create_entities(records=db_models)
