import uuid
from datetime import datetime, timezone

from sqlalchemy import DateTime, ForeignKey, Index, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class Chamado(Base):
    """Cliente apertou "Chamar garçom". Fica aberto até alguém do salão atender."""

    __tablename__ = "chamado"
    __table_args__ = (
        # No máximo um chamado aberto por mesa: apertar o botão de novo não gera spam.
        Index("uq_chamado_aberto_por_mesa", "mesa_id", unique=True, postgresql_where=text("atendido_em IS NULL")),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    mesa_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("mesa.id"), nullable=False)
    comanda_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("comanda.id"), nullable=True
    )
    criado_em: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc)
    )
    atendido_em: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    atendido_por: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("funcionario.id"), nullable=True
    )
