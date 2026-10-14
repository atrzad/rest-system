import uuid
from decimal import Decimal

from pydantic import BaseModel

from app.models.comanda import ComandaStatus
from app.schemas.pedido import PedidoOut


class ProdutoPublicoOut(BaseModel):
    id: uuid.UUID
    nome: str
    categoria: str
    preco: Decimal


class ComandaPublicaOut(BaseModel):
    id: uuid.UUID
    status: ComandaStatus


class MesaPublicaOut(BaseModel):
    """O que o cliente vê na própria mesa: cardápio, comanda aberta, pedidos e se já chamou o garçom."""

    numero: int
    cardapio: list[ProdutoPublicoOut]
    comanda: ComandaPublicaOut | None
    pedidos: list[PedidoOut]
    chamado_aberto: bool
