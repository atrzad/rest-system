import enum
import uuid
from datetime import datetime, timezone

from sqlalchemy import DateTime, Enum, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class PedidoStatus(str, enum.Enum):
    recebido = "recebido"
    em_preparo = "em_preparo"
    pronto = "pronto"
    entregue = "entregue"
    cancelado = "cancelado"


class Pedido(Base):
    __tablename__ = "pedido"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    comanda_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("comanda.id"), nullable=False, index=True
    )
    status: Mapped[PedidoStatus] = mapped_column(
        Enum(PedidoStatus, name="pedido_status"), nullable=False, default=PedidoStatus.recebido
    )
    criado_em: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc)
    )
    atualizado_em: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )
