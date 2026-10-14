import uuid

from pydantic import BaseModel, ConfigDict


class MesaCreate(BaseModel):
    numero: int
    capacidade: int | None = None


class MesaUpdate(BaseModel):
    capacidade: int | None = None
    ativa: bool | None = None


class MesaOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    numero: int
    capacidade: int | None
    ativa: bool
    # Só preenchido para admin (é o segredo do QR); o salão recebe None.
    token: str | None = None
    url_qr: str | None = None
