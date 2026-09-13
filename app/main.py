from fastapi import FastAPI

from app.routers import embeddings, scrape

app = FastAPI(title="Elden RAG")
app.include_router(scrape.router)
app.include_router(embeddings.router)
