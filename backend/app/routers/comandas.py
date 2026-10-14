import uuid

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.deps import require_role
from app.db.session import get_db
from app.models.comanda import Comanda, ComandaStatus, OrigemAbertura
from app.models.mesa import Mesa
from app.models.roles import Role
from app.schemas.comanda import AbrirComandaRequest, ComandaOut, ContaOut, FecharComandaRequest
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
        subtotal=comanda.subtotal,
        taxa_servico=comanda.taxa_servico,
        total=comanda.total,
    )


@router.post(
    "/abrir-por-mesa", response_model=ComandaOut, dependencies=[Depends(require_role(Role.admin, Role.salao))]
)
async def abrir_por_mesa(dados: AbrirComandaRequest, db: AsyncSession = Depends(get_db)) -> ComandaOut:
    """Abertura pelo garçom. O cliente abre pela rota pública /publico/mesas/{numero}/comanda (com token)."""
    comanda = await comanda_service.abrir_por_mesa(db, dados.numero_mesa, OrigemAbertura.garcom)
    return _to_out(comanda, dados.numero_mesa)


@router.get("", response_model=list[ComandaOut], dependencies=[Depends(require_role(Role.admin, Role.salao))])
async def listar(status_filtro: ComandaStatus | None = None, db: AsyncSession = Depends(get_db)) -> list[ComandaOut]:
    query = select(Comanda, Mesa.numero).join(Mesa, Comanda.mesa_id == Mesa.id)
    if status_filtro is not None:
        query = query.where(Comanda.status == status_filtro)
    query = query.order_by(Mesa.numero)

    resultado = await db.execute(query)
    return [_to_out(comanda, mesa_numero) for comanda, mesa_numero in resultado.all()]


@router.get(
    "/{comanda_id}/conta", response_model=ContaOut, dependencies=[Depends(require_role(Role.admin, Role.salao))]
)
async def conta(comanda_id: uuid.UUID, taxa: bool = True, db: AsyncSession = Depends(get_db)) -> ContaOut:
    comanda = await comanda_service.obter(db, comanda_id)
    return await comanda_service.calcular_conta(db, comanda, taxa)


@router.post(
    "/{comanda_id}/fechar", response_model=ComandaOut, dependencies=[Depends(require_role(Role.admin, Role.salao))]
)
async def fechar(
    comanda_id: uuid.UUID,
    dados: FecharComandaRequest | None = None,
    db: AsyncSession = Depends(get_db),
) -> ComandaOut:
    com_taxa = dados.taxa_servico if dados is not None else True
    comanda = await comanda_service.fechar(db, comanda_id, com_taxa)
    mesa = await db.get(Mesa, comanda.mesa_id)
    return _to_out(comanda, mesa.numero)
