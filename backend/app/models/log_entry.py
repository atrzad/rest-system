from datetime import datetime, timezone

from sqlalchemy import BigInteger, Boolean, DateTime, LargeBinary, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class LogEntry(Base):
    """Log interno (eventos do sistema + exceções não tratadas). Sem endpoint HTTP —
    consulta só via terminal/SSH com acesso direto ao banco (ver app/scripts/ler_logs.py)."""

    __tablename__ = "log_entry"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    nivel: Mapped[str] = mapped_column(String(10), nullable=False, index=True)
    logger_nome: Mapped[str] = mapped_column(String(120), nullable=False)
    mensagem: Mapped[bytes] = mapped_column(LargeBinary, nullable=False)
    mensagem_comprimida: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    contexto: Mapped[bytes | None] = mapped_column(LargeBinary, nullable=True)
    contexto_comprimida: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    criado_em: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc), index=True
    )
