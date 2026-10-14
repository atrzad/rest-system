import uuid
from datetime import datetime

from pydantic import BaseModel


class ChamadoOut(BaseModel):
    id: uuid.UUID
    mesa_numero: int
    comanda_id: uuid.UUID | None
    criado_em: datetime
    atendido_em: datetime | None
