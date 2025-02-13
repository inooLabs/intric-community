from typing import TYPE_CHECKING, Optional

if TYPE_CHECKING:
    from datetime import datetime
    from uuid import UUID

    from intric.ai_models.embedding_models.embedding_model import EmbeddingModel
    from intric.users.user import UserInDBBase


# Prepared but not used yet
class _Group:
    def __init__(
        self,
        name: str,
        space_id: "UUID",
        embedding_model: "EmbeddingModel",
        user: "UserInDBBase",
        created_at: Optional["datetime"] = None,
        updated_at: Optional["datetime"] = None,
        id: Optional["UUID"] = None,
        published: bool = False,
        num_info_blobs: int = 0,
    ):
        self.id = id
        self.created_at = created_at
        self.updated_at = updated_at
        self.name = name
        self.space_id = space_id
        self.published = published
        self.embedding_model = embedding_model
        self.user = user
        self.num_info_blobs = num_info_blobs
