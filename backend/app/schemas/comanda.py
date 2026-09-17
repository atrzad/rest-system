import uuid
from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict

from app.models.comanda import ComandaStatus, OrigemAbertura


class AbrirComandaRequest(BaseModel):
    numero_mesa: int
    origem: OrigemAbertura


class ComandaOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    mesa_id: uuid.UUID
    mesa_numero: int
    status: ComandaStatus
    aberta_por: OrigemAbertura
    aberta_em: datetime
    fechada_em: datetime | None
    total: Decimal | None
