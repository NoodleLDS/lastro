from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="LASTRO_", env_file=".env")

    database_url: str = "sqlite+aiosqlite:///./lastro.db"
    llm_provider: str = "ollama"
    ollama_url: str = "http://localhost:11434"
    ollama_model: str = "llama3.2:3b"
    anthropic_api_key: str | None = None
    brapi_token: str | None = None


settings = Settings()
