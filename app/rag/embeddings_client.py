import requests

from app.core.config import settings


def embed_via_api(texts: str | list[str]) -> list[list[float]]:
    resp = requests.post(
        f"{settings.api_base_url}/embeddings/embed",
        json={"inputs": texts},
        timeout=30,
    )
    resp.raise_for_status()
    return resp.json()["embeddings"]
