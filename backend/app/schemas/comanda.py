import uuid
from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict

from app.models.comanda import ComandaStatus, OrigemAbertura


class AbrirComandaRequest(BaseModel):
    numero_mesa: int
    origem: OrigemAbertura


class FecharComandaRequest(BaseModel):
    taxa_servico: bool = True


class ComandaOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    mesa_id: uuid.UUID
    mesa_numero: int
    status: ComandaStatus
    aberta_por: OrigemAbertura
    aberta_em: datetime
    fechada_em: datetime | None
    subtotal: Decimal | None
    taxa_servico: Decimal | None
    total: Decimal | None


class ContaItemOut(BaseModel):
    produto_id: uuid.UUID
    produto_nome: str
    preco_unitario: Decimal
    quantidade: int
    valor: Decimal


class ContaOut(BaseModel):
    comanda_id: uuid.UUID
    mesa_numero: int
    itens: list[ContaItemOut]
    subtotal: Decimal
    taxa_servico: Decimal
    total: Decimal
    pedidos_pendentes: int
