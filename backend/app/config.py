from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file="../.env", env_file_encoding="utf-8", extra="ignore")

    database_url: str = "postgresql+asyncpg://rest_system:rest_system@localhost:5432/rest_system"
    redis_url: str = "redis://localhost:6379/0"
    jwt_secret: str = "troque-isto-por-um-segredo-forte"
    jwt_expire_minutes: int = 480
    cors_origins: str = "http://localhost:5173"
    # Endereço do frontend que o cliente acessa pelo QR da mesa (vai dentro do QR code).
    public_base_url: str = "http://localhost:5173"
    # Fuso usado para "hoje", "por hora" e "por dia" no dashboard.
    timezone_local: str = "America/Manaus"
    # Canal do Redis Pub/Sub. O pub/sub ignora o número do banco do Redis, então dev e produção
    # na mesma instância precisam de canais diferentes para não trocarem eventos entre si.
    canal_eventos: str = "eventos:all"
    # /docs e /openapi.json (Swagger). Desligar em produção pública.
    expor_docs: bool = True
    # Pasta do build do frontend (frontend/dist). Se existir, a API também serve o site (mesma origem).
    frontend_dist: str = ""

    @property
    def cors_origins_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]


settings = Settings()
