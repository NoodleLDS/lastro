from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="LASTRO_", env_file=".env")

    database_url: str = "sqlite+aiosqlite:///./lastro.db"
    llm_provider: str = "ollama"
    ollama_url: str = "http://localhost:11434"
    ollama_model: str = "llama3.2:3b"
    ollama_vision_model: str = "qwen2.5vl:3b"
    anthropic_api_key: str | None = None
    brapi_token: str | None = None
    launcher_url: str = "http://host.docker.internal:9100"
    admin_username: str = "admin"
    admin_password: str = "admin"
    jwt_secret: str = "lastro-dev-secret-change-me"
    jwt_expire_minutes: int = 60 * 24 * 7
    demo_mode: bool = False
    demo_reset_secret: str | None = None


settings = Settings()
