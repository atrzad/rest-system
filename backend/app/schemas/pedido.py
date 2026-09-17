import uuid
from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field

from app.models.pedido import PedidoStatus


class PedidoItemCreate(BaseModel):
    produto_id: uuid.UUID
    quantidade: int = Field(gt=0)
    observacao: str | None = None


class PedidoCreate(BaseModel):
    comanda_id: uuid.UUID
    itens: list[PedidoItemCreate] = Field(min_length=1)


class PedidoStatusUpdate(BaseModel):
    status: PedidoStatus


class PedidoItemOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    produto_id: uuid.UUID
    produto_nome: str
    quantidade: int
    preco_unitario: Decimal
    observacao: str | None


class PedidoOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    comanda_id: uuid.UUID
    mesa_numero: int
    status: PedidoStatus
    criado_em: datetime
    atualizado_em: datetime
    itens: list[PedidoItemOut]
