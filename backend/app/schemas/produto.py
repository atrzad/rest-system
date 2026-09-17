import uuid
from decimal import Decimal

from pydantic import BaseModel, ConfigDict


class ProdutoCreate(BaseModel):
    nome: str
    categoria: str
    preco: Decimal
    disponivel: bool = True


class ProdutoUpdate(BaseModel):
    nome: str | None = None
    categoria: str | None = None
    preco: Decimal | None = None
    disponivel: bool | None = None


class ProdutoOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    nome: str
    categoria: str
    preco: Decimal
    disponivel: bool
