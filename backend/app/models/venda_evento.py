import uuid
from datetime import datetime, timezone
from decimal import Decimal
from typing import Any

from sqlalchemy import BigInteger, DateTime, ForeignKey, Integer, Numeric, String
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class VendaEvento(Base):
    """Fato imutável (append-only) para o dashboard, gravado na mesma transação da mudança de negócio.

    Tipos: pedido_item_criado, pedido_item_cancelado (quantidade/valor negativos),
    pedido_status (payload de/para) e comanda_fechada (valor = total).
    """

    __tablename__ = "venda_evento"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    tipo: Mapped[str] = mapped_column(String(40), nullable=False, index=True)
    comanda_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("comanda.id"), nullable=True)
    pedido_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("pedido.id"), nullable=True)
    produto_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("produto.id"), nullable=True)
    valor: Mapped[Decimal | None] = mapped_column(Numeric(10, 2), nullable=True)
    quantidade: Mapped[int | None] = mapped_column(Integer, nullable=True)
    ocorrido_em: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc), index=True
    )
    payload: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False, default=dict)
