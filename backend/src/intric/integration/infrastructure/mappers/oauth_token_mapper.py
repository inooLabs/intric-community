from typing import Any, Dict, List

from intric.base.base_entity import EntityMapper
from intric.database.tables.integration_table import (
    OauthToken as OauthTokenDBModel,
)
from intric.integration.domain.entities.oauth_token import OauthToken
from intric.integration.domain.factories.oauth_token_factory import (
    OauthTokenFactory,
)


class OauthTokenMapper(EntityMapper[OauthToken, OauthTokenDBModel]):
    def to_db_dict(self, entity: OauthToken) -> Dict[str, Any]:
        return {
            "access_token": entity.access_token,
            "refresh_token": entity.refresh_token,
            "token_type": entity.token_type.value,
            "user_integration_id": entity.user_integration.id,
            "resources": entity.resources,
        }

    def to_entity(self, db_model: OauthTokenDBModel) -> OauthToken:
        return OauthTokenFactory.create_entity(record=db_model)

    def to_entities(
        self, db_models: List[OauthTokenDBModel]
    ) -> List[OauthToken]:
        pass
