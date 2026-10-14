import uuid

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.deps import require_role
from app.db.session import get_db
from app.models.roles import Role
from app.schemas.auth import CurrentUser
from app.schemas.chamado import ChamadoOut
from app.services import chamado_service

staff = require_role(Role.admin, Role.salao)

router = APIRouter(prefix="/chamados", tags=["chamados"], dependencies=[Depends(staff)])


@router.get("", response_model=list[ChamadoOut])
async def listar_abertos(db: AsyncSession = Depends(get_db)) -> list[ChamadoOut]:
    return await chamado_service.listar_abertos(db)


@router.post("/{chamado_id}/atender", response_model=ChamadoOut)
async def atender(
    chamado_id: uuid.UUID, user: CurrentUser = Depends(staff), db: AsyncSession = Depends(get_db)
) -> ChamadoOut:
    return await chamado_service.atender(db, chamado_id, uuid.UUID(user.id))
