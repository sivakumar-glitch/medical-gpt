from sentence_transformers import SentenceTransformer
from functools import lru_cache

from ..core.config import settings

class EmbeddingService:
    def __init__(self, model_name: str = settings.EMBEDDING_MODEL_NAME):
        self.model = SentenceTransformer(model_name)

    def encode(self, texts: list[str]) -> list[list[float]]:
        # normalize_embeddings=True improves cosine similarity search
        embeddings = self.model.encode(texts, normalize_embeddings=True)
        return embeddings.tolist()

@lru_cache()
def get_embedding_service():
    return EmbeddingService()
