from datetime import date
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel


class PontoSerie(BaseModel):
    rotulo: str  # "19h" ou "13/10"
    inicio: str  # início do intervalo no horário local, ISO sem fuso (ex.: "2026-10-13T19:00:00")
    valor: Decimal
    itens: int


class ProdutoRanking(BaseModel):
    produto_id: str
    nome: str
    quantidade: int
    valor: Decimal


class CategoriaVenda(BaseModel):
    categoria: str
    quantidade: int
    valor: Decimal


class DashboardVendas(BaseModel):
    inicio: date
    fim: date
    fuso: str
    faturamento: Decimal  # soma das comandas fechadas (com taxa de serviço)
    taxa_servico: Decimal
    comandas_fechadas: int
    ticket_medio: Decimal
    comandas_abertas_agora: int
    consumo: Decimal  # itens lançados menos cancelados (inclui comandas ainda abertas)
    itens_vendidos: int
    tempo_medio_preparo_min: float | None
    granularidade: Literal["hora", "dia"]
    serie: list[PontoSerie]
    top_produtos: list[ProdutoRanking]
    por_categoria: list[CategoriaVenda]
