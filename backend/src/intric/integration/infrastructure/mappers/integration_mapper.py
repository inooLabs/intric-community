from typing import Any, Dict, List

from intric.base.base_entity import EntityMapper
from intric.database.tables.integration_table import Integration as IntegrationDBModel
from intric.integration.domain.entities.integration import Integration
from intric.integration.domain.factories.integration_factory import IntegrationFactory


class IntegrationMapper(EntityMapper[Integration, IntegrationDBModel]):
    def to_db_dict(self, entity: Integration) -> Dict[str, Any]:
        return {
            "name": entity.name,
            "description": entity.description,
            "integration_type": entity.integration_type,
        }

    def to_entity(self, db_model: IntegrationDBModel) -> Integration:
        return IntegrationFactory.create_entity(record=db_model)

    def to_entities(self, db_models: List[IntegrationDBModel]) -> List[Integration]:
        return IntegrationFactory.create_entities(records=db_models)
