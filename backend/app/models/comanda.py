import enum
import uuid
from datetime import datetime, timezone
from decimal import Decimal

from sqlalchemy import DateTime, Enum, ForeignKey, Index, Numeric, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class ComandaStatus(str, enum.Enum):
    aberta = "aberta"
    fechada = "fechada"


class OrigemAbertura(str, enum.Enum):
    cliente_qr = "cliente_qr"
    cliente_manual = "cliente_manual"
    garcom = "garcom"


class Comanda(Base):
    __tablename__ = "comanda"
    __table_args__ = (
        # Garante no banco que cada mesa tem no máximo uma comanda aberta (evita corrida na abertura).
        Index("uq_comanda_aberta_por_mesa", "mesa_id", unique=True, postgresql_where=text("status = 'aberta'")),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    mesa_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("mesa.id"), nullable=False, index=True)
    status: Mapped[ComandaStatus] = mapped_column(
        Enum(ComandaStatus, name="comanda_status"), nullable=False, default=ComandaStatus.aberta
    )
    aberta_por: Mapped[OrigemAbertura] = mapped_column(Enum(OrigemAbertura, name="origem_abertura"), nullable=False)
    aberta_em: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc)
    )
    fechada_em: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    subtotal: Mapped[Decimal | None] = mapped_column(Numeric(10, 2), nullable=True)
    taxa_servico: Mapped[Decimal | None] = mapped_column(Numeric(10, 2), nullable=True)
    total: Mapped[Decimal | None] = mapped_column(Numeric(10, 2), nullable=True)
