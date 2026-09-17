import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr

from app.models.roles import Role


class FuncionarioCreate(BaseModel):
    nome: str
    email: EmailStr
    senha: str
    role: Role


class FuncionarioUpdate(BaseModel):
    nome: str | None = None
    role: Role | None = None
    ativo: bool | None = None


class FuncionarioOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    nome: str
    email: str
    role: Role
    ativo: bool
    criado_em: datetime
