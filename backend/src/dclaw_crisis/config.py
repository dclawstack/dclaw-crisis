from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    app_name: str = "DClaw Crisis"
    database_url: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/dclaw_crisis"
    cors_origins: str = "*"

    class Config:
        env_prefix = "CRISIS_"

settings = Settings()
