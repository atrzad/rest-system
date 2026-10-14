from datetime import date, timedelta

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.deps import require_role
from app.db.session import get_db
from app.models.roles import Role
from app.schemas.dashboard import DashboardVendas
from app.services import dashboard_service

router = APIRouter(prefix="/dashboard", tags=["dashboard"], dependencies=[Depends(require_role(Role.admin))])

MAX_DIAS = 366


@router.get("/vendas", response_model=DashboardVendas)
async def vendas(
    inicio: date | None = None,
    fim: date | None = None,
    dias: int | None = Query(default=None, ge=1, le=MAX_DIAS),
    db: AsyncSession = Depends(get_db),
) -> DashboardVendas:
    """Período em datas locais (inclusive nas duas pontas). Sem parâmetros: hoje.

    `dias=7` é atalho para "os últimos 7 dias até hoje", calculado no fuso do restaurante.
    """
    hoje = dashboard_service.hoje_local()
    fim = fim or hoje
    inicio = inicio or (fim - timedelta(days=dias - 1) if dias else fim)
    if inicio > fim:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "A data inicial é depois da final")
    if fim - inicio > timedelta(days=MAX_DIAS):
        raise HTTPException(status.HTTP_400_BAD_REQUEST, f"Período máximo é de {MAX_DIAS} dias")
    return await dashboard_service.vendas(db, inicio, fim)
