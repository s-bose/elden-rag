from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    redis_url: str = "redis://localhost:6379/0"
    postgres_host: str = "localhost"
    postgres_port: int = 5432
    postgres_user: str = "tarnished"
    postgres_pass: str = "tarnished"
    postgres_db: str = "tarnished"
    scraper_base_url: str = Field("https://eldenring.wiki.fextralife.com")
    scraper_user_agent: str = Field(
        "Mozilla/5.0 (compatible; EldenRagBot/0.1; local research project)"
    )

    hf_token: str | None = Field(None)
    scraper_rate_limit: str = Field("30/m")
    scraper_run_ttl_seconds: int = Field(60 * 60 * 24 * 3)
    embedding_model_id: str = Field("BAAI/bge-small-en-v1.5")
    api_base_url: str = Field("http://localhost:8000")


    model_config = SettingsConfigDict(
        case_sensitive=False,
        env_file_encoding="utf-8",
    )


settings = Settings()
