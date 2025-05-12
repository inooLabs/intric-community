from typing import TYPE_CHECKING

from intric.ai_models.model_enums import ModelFamily
from intric.embedding_models.infrastructure.adapters.base import EmbeddingModelAdapter
from intric.embedding_models.infrastructure.adapters.e5_embeddings import E5Adapter
from intric.embedding_models.infrastructure.adapters.openai_embeddings import (
    OpenAIEmbeddingAdapter,
)
from intric.files.chunk_embedding_list import ChunkEmbeddingList
from intric.info_blobs.info_blob import InfoBlobChunk

if TYPE_CHECKING:
    from intric.embedding_models.domain.embedding_model import EmbeddingModel


class CreateEmbeddingsService:
    def __init__(self):
        self._adapters = {
            ModelFamily.OPEN_AI: OpenAIEmbeddingAdapter,
            ModelFamily.E5: E5Adapter,
        }

    def _get_adapter(self, model: "EmbeddingModel") -> EmbeddingModelAdapter:
        adapter_class = self._adapters.get(model.family.value)
        if not adapter_class:
            raise ValueError(f"No adapter found for hosting {model.family.value}")

        return adapter_class(model)

    async def get_embeddings(
        self,
        model: "EmbeddingModel",
        chunks: list[InfoBlobChunk],
    ) -> ChunkEmbeddingList:
        adapter = self._get_adapter(model)
        return await adapter.get_embeddings(chunks)

    async def get_embedding_for_query(
        self,
        model: "EmbeddingModel",
        query: str,
    ) -> list[float]:
        adapter = self._get_adapter(model)
        return await adapter.get_embedding_for_query(query)
