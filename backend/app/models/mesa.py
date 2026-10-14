import secrets
import uuid

from sqlalchemy import Boolean, Integer, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base

# Sem 0/O/1/I para o código impresso abaixo do QR poder ser digitado sem confusão.
ALFABETO_TOKEN = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"
TAMANHO_TOKEN = 6


def gerar_token_mesa() -> str:
    return "".join(secrets.choice(ALFABETO_TOKEN) for _ in range(TAMANHO_TOKEN))


class Mesa(Base):
    __tablename__ = "mesa"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    numero: Mapped[int] = mapped_column(Integer, nullable=False, unique=True, index=True)
    capacidade: Mapped[int | None] = mapped_column(Integer, nullable=True)
    ativa: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    # Segredo que vai no QR fixo (/mesa/12?t=TOKEN): sem ele, as rotas públicas da mesa respondem 404.
    token: Mapped[str] = mapped_column(String(12), nullable=False, unique=True, default=gerar_token_mesa)
