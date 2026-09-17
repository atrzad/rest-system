from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file="../.env", env_file_encoding="utf-8", extra="ignore")

    database_url: str = "postgresql+asyncpg://rest_system:rest_system@localhost:5432/rest_system"
    redis_url: str = "redis://localhost:6379/0"
    jwt_secret: str = "troque-isto-por-um-segredo-forte"
    jwt_expire_minutes: int = 480
    cors_origins: str = "http://localhost:5173"

    @property
    def cors_origins_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]


settings = Settings()
