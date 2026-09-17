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
