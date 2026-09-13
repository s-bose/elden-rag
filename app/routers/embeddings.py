from fastapi import APIRouter
from pydantic import BaseModel

from app.rag.embeddings import embedding_model

router = APIRouter(prefix="/embeddings")


class EmbedRequest(BaseModel):
    inputs: str | list[str]


class EmbedResponse(BaseModel):
    embeddings: list[list[float]]


@router.post("/embed")
def embed(request: EmbedRequest) -> EmbedResponse:
    return EmbedResponse(embeddings=embedding_model.embed(request.inputs))
