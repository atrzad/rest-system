import uuid

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.deps import require_role
from app.db.session import get_db
from app.models.pedido import PedidoStatus
from app.models.roles import Role
from app.schemas.pedido import PedidoCreate, PedidoOut, PedidoStatusUpdate
from app.services import pedido_service

router = APIRouter(
    prefix="/pedidos",
    tags=["pedidos"],
    dependencies=[Depends(require_role(Role.admin, Role.salao, Role.cozinha))],
)


@router.post("", response_model=PedidoOut, status_code=status.HTTP_201_CREATED)
async def criar(dados: PedidoCreate, db: AsyncSession = Depends(get_db)) -> PedidoOut:
    return await pedido_service.criar_pedido(db, dados.comanda_id, dados.itens)


@router.get("", response_model=list[PedidoOut])
async def listar(
    status_filtro: PedidoStatus | None = None,
    comanda_id: uuid.UUID | None = None,
    db: AsyncSession = Depends(get_db),
) -> list[PedidoOut]:
    return await pedido_service.listar(db, status_filtro, comanda_id)


@router.patch("/{pedido_id}/status", response_model=PedidoOut)
async def atualizar_status(
    pedido_id: uuid.UUID, dados: PedidoStatusUpdate, db: AsyncSession = Depends(get_db)
) -> PedidoOut:
    return await pedido_service.atualizar_status(db, pedido_id, dados.status)
