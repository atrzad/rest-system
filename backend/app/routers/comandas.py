import uuid

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.deps import require_role
from app.db.session import get_db
from app.models.comanda import Comanda, ComandaStatus
from app.models.mesa import Mesa
from app.models.roles import Role
from app.schemas.comanda import AbrirComandaRequest, ComandaOut
from app.services import comanda_service

router = APIRouter(prefix="/comandas", tags=["comandas"])


def _to_out(comanda: Comanda, mesa_numero: int) -> ComandaOut:
    return ComandaOut(
        id=comanda.id,
        mesa_id=comanda.mesa_id,
        mesa_numero=mesa_numero,
        status=comanda.status,
        aberta_por=comanda.aberta_por,
        aberta_em=comanda.aberta_em,
        fechada_em=comanda.fechada_em,
        total=comanda.total,
    )


@router.post("/abrir-por-mesa", response_model=ComandaOut)
async def abrir_por_mesa(dados: AbrirComandaRequest, db: AsyncSession = Depends(get_db)) -> ComandaOut:
    comanda = await comanda_service.abrir_por_mesa(db, dados.numero_mesa, dados.origem)
    return _to_out(comanda, dados.numero_mesa)


@router.get("", response_model=list[ComandaOut], dependencies=[Depends(require_role(Role.admin, Role.salao))])
async def listar(status_filtro: ComandaStatus | None = None, db: AsyncSession = Depends(get_db)) -> list[ComandaOut]:
    query = select(Comanda, Mesa.numero).join(Mesa, Comanda.mesa_id == Mesa.id)
    if status_filtro is not None:
        query = query.where(Comanda.status == status_filtro)
    query = query.order_by(Mesa.numero)

    resultado = await db.execute(query)
    return [_to_out(comanda, mesa_numero) for comanda, mesa_numero in resultado.all()]


@router.post(
    "/{comanda_id}/fechar", response_model=ComandaOut, dependencies=[Depends(require_role(Role.admin, Role.salao))]
)
async def fechar(comanda_id: uuid.UUID, db: AsyncSession = Depends(get_db)) -> ComandaOut:
    comanda = await comanda_service.fechar(db, comanda_id)
    mesa = await db.get(Mesa, comanda.mesa_id)
    return _to_out(comanda, mesa.numero)
