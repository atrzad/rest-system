import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.deps import require_role
from app.db.session import get_db
from app.models.mesa import Mesa
from app.models.roles import Role
from app.schemas.mesa import MesaCreate, MesaOut, MesaUpdate

router = APIRouter(
    prefix="/mesas",
    tags=["mesas"],
    dependencies=[Depends(require_role(Role.admin, Role.salao))],
)


@router.get("", response_model=list[MesaOut])
async def listar(db: AsyncSession = Depends(get_db)) -> list[Mesa]:
    resultado = await db.execute(select(Mesa).order_by(Mesa.numero))
    return list(resultado.scalars().all())


@router.post(
    "", response_model=MesaOut, status_code=status.HTTP_201_CREATED, dependencies=[Depends(require_role(Role.admin))]
)
async def criar(dados: MesaCreate, db: AsyncSession = Depends(get_db)) -> Mesa:
    existente = await db.execute(select(Mesa).where(Mesa.numero == dados.numero))
    if existente.scalar_one_or_none() is not None:
        raise HTTPException(status.HTTP_409_CONFLICT, "Já existe uma mesa com este número")

    mesa = Mesa(**dados.model_dump())
    db.add(mesa)
    await db.commit()
    await db.refresh(mesa)
    return mesa


@router.patch("/{mesa_id}", response_model=MesaOut, dependencies=[Depends(require_role(Role.admin))])
async def atualizar(mesa_id: uuid.UUID, dados: MesaUpdate, db: AsyncSession = Depends(get_db)) -> Mesa:
    mesa = await db.get(Mesa, mesa_id)
    if mesa is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Mesa não encontrada")

    for campo, valor in dados.model_dump(exclude_unset=True).items():
        setattr(mesa, campo, valor)

    await db.commit()
    await db.refresh(mesa)
    return mesa
