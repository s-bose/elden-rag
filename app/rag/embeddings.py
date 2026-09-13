from sentence_transformers import SentenceTransformer

from app.core.config import settings


class EmbeddingModel:
    _instance: "EmbeddingModel | None" = None
    _model: SentenceTransformer

    def __new__(cls) -> "EmbeddingModel":
        if cls._instance is None:
            instance = super().__new__(cls)
            instance._model = SentenceTransformer(settings.embedding_model_id)
            cls._instance = instance
        return cls._instance

    def embed(self, texts: str | list[str]) -> list[list[float]]:
        inputs = [texts] if isinstance(texts, str) else texts
        vectors = self._model.encode(inputs, normalize_embeddings=True)
        return vectors.tolist()


embedding_model = EmbeddingModel()
