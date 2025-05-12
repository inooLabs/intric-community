from typing import TYPE_CHECKING, Optional

from intric.ai_models.model_enums import (
    ModelFamily,
    ModelHostingLocation,
    ModelOrg,
    ModelStability,
)
from intric.base.base_entity import Entity
from intric.modules.module import Modules

if TYPE_CHECKING:
    from datetime import datetime
    from uuid import UUID

    from intric.security_classifications.domain.entities.security_classification import (
        SecurityClassification,
    )
    from intric.users.user import UserInDB


class AIModel(Entity):
    def __init__(
        self,
        *,
        user: "UserInDB",
        nickname: Optional[str],
        name: str,
        family: ModelFamily,
        hosting: ModelHostingLocation,
        org: Optional[ModelOrg],
        stability: ModelStability,
        open_source: bool,
        description: Optional[str],
        hf_link: Optional[str],
        is_deprecated: bool,
        is_org_enabled: bool,
        id: Optional["UUID"] = None,
        created_at: Optional["datetime"] = None,
        updated_at: Optional["datetime"] = None,
        security_classification: Optional["SecurityClassification"] = None,
    ):
        super().__init__(id, created_at, updated_at)
        self.user = user
        self.nickname = nickname
        self.name = name
        self.family = ModelFamily(family)
        self.hosting = ModelHostingLocation(hosting)
        self.org = ModelOrg(org) if org else None
        self.stability = ModelStability(stability)
        self.open_source = open_source
        self.description = description
        self.hf_link = hf_link
        self.is_deprecated = is_deprecated
        self.is_org_enabled = is_org_enabled
        self.security_classification = security_classification

    @property
    def is_locked(self):
        if self.hosting == ModelHostingLocation.EU:
            if Modules.EU_HOSTING not in self.user.modules:
                return True

        if self.hosting == ModelHostingLocation.SWE:
            if Modules.SWE_HOSTING not in self.user.modules:
                return True

        return False

    @property
    def can_access(self):
        return not self.is_locked and not self.is_deprecated and self.is_org_enabled

    def meets_security_classification(
        self, security_classification: Optional["SecurityClassification"] = None
    ):
        if security_classification is None:
            return True
        else:
            if self.security_classification is None:
                return False

            return (
                self.security_classification.security_level
                >= security_classification.security_level
            )
