"""Grava os fatos de venda (tabela venda_evento) usados pelo dashboard.

Sempre chamado antes do commit da operação de negócio, na mesma sessão: o fato e a
mudança entram juntos ou nenhum entra (não depende do Redis estar no ar).
"""

import uuid
from decimal import Decimal
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.venda_evento import VendaEvento


def registrar(
    db: AsyncSession,
    tipo: str,
    *,
    comanda_id: uuid.UUID | None = None,
    pedido_id: uuid.UUID | None = None,
    produto_id: uuid.UUID | None = None,
    valor: Decimal | None = None,
    quantidade: int | None = None,
    payload: dict[str, Any] | None = None,
) -> None:
    db.add(
        VendaEvento(
            tipo=tipo,
            comanda_id=comanda_id,
            pedido_id=pedido_id,
            produto_id=produto_id,
            valor=valor,
            quantidade=quantidade,
            payload=payload or {},
        )
    )
