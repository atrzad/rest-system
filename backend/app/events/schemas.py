import uuid
from datetime import datetime, timezone
from typing import Any

from pydantic import BaseModel, Field


class EventoEnvelope(BaseModel):
    tipo: str
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    ocorrido_em: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    mesa_numero: int | None = None
    comanda_id: str | None = None
    payload: dict[str, Any] = Field(default_factory=dict)
