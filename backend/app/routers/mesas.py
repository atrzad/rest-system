import io
import uuid

import qrcode
from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.deps import require_role
from app.config import settings
from app.db.session import get_db
from app.models.mesa import Mesa, gerar_token_mesa
from app.models.roles import Role
from app.schemas.auth import CurrentUser
from app.schemas.mesa import MesaCreate, MesaOut, MesaUpdate

staff = require_role(Role.admin, Role.salao)
somente_admin = require_role(Role.admin)

router = APIRouter(prefix="/mesas", tags=["mesas"], dependencies=[Depends(staff)])


def url_qr(mesa: Mesa) -> str:
    return f"{settings.public_base_url.rstrip('/')}/mesa/{mesa.numero}?t={mesa.token}"


def _to_out(mesa: Mesa, com_token: bool) -> MesaOut:
    return MesaOut(
        id=mesa.id,
        numero=mesa.numero,
        capacidade=mesa.capacidade,
        ativa=mesa.ativa,
        token=mesa.token if com_token else None,
        url_qr=url_qr(mesa) if com_token else None,
    )


async def _obter(db: AsyncSession, mesa_id: uuid.UUID) -> Mesa:
    mesa = await db.get(Mesa, mesa_id)
    if mesa is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Mesa não encontrada")
    return mesa


@router.get("", response_model=list[MesaOut])
async def listar(user: CurrentUser = Depends(staff), db: AsyncSession = Depends(get_db)) -> list[MesaOut]:
    resultado = await db.execute(select(Mesa).order_by(Mesa.numero))
    return [_to_out(mesa, com_token=user.role == Role.admin) for mesa in resultado.scalars().all()]


@router.post("", response_model=MesaOut, status_code=status.HTTP_201_CREATED, dependencies=[Depends(somente_admin)])
async def criar(dados: MesaCreate, db: AsyncSession = Depends(get_db)) -> MesaOut:
    existente = await db.execute(select(Mesa).where(Mesa.numero == dados.numero))
    if existente.scalar_one_or_none() is not None:
        raise HTTPException(status.HTTP_409_CONFLICT, "Já existe uma mesa com este número")

    mesa = Mesa(**dados.model_dump())
    db.add(mesa)
    await db.commit()
    await db.refresh(mesa)
    return _to_out(mesa, com_token=True)


@router.patch("/{mesa_id}", response_model=MesaOut, dependencies=[Depends(somente_admin)])
async def atualizar(mesa_id: uuid.UUID, dados: MesaUpdate, db: AsyncSession = Depends(get_db)) -> MesaOut:
    mesa = await _obter(db, mesa_id)
    for campo, valor in dados.model_dump(exclude_unset=True).items():
        setattr(mesa, campo, valor)

    await db.commit()
    await db.refresh(mesa)
    return _to_out(mesa, com_token=True)


@router.post("/{mesa_id}/regenerar-token", response_model=MesaOut, dependencies=[Depends(somente_admin)])
async def regenerar_token(mesa_id: uuid.UUID, db: AsyncSession = Depends(get_db)) -> MesaOut:
    """Invalida o QR impresso atual (ex.: foi fotografado e compartilhado). É preciso imprimir de novo."""
    mesa = await _obter(db, mesa_id)
    mesa.token = gerar_token_mesa()
    await db.commit()
    await db.refresh(mesa)
    return _to_out(mesa, com_token=True)


@router.get("/{mesa_id}/qrcode.png", dependencies=[Depends(somente_admin)])
async def qrcode_png(mesa_id: uuid.UUID, db: AsyncSession = Depends(get_db)) -> Response:
    mesa = await _obter(db, mesa_id)
    buffer = io.BytesIO()
    qrcode.make(url_qr(mesa), box_size=10, border=2).save(buffer, format="PNG")
    return Response(content=buffer.getvalue(), media_type="image/png")
