"""Rotas do cliente na mesa (self-view). Sem login: a "identidade" é o número da mesa + o token do QR."""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.models.comanda import Comanda, ComandaStatus
from app.models.produto import Produto
from app.schemas.chamado import ChamadoOut
from app.schemas.comanda import AbrirComandaPublicaRequest, ContaOut
from app.schemas.publico import ComandaPublicaOut, MesaPublicaOut, ProdutoPublicoOut
from app.services import chamado_service, comanda_service, mesa_service, pedido_service

router = APIRouter(prefix="/publico/mesas/{numero}", tags=["público (cliente)"])


async def _comanda_aberta(db: AsyncSession, mesa_id) -> Comanda | None:
    resultado = await db.execute(
        select(Comanda).where(Comanda.mesa_id == mesa_id, Comanda.status == ComandaStatus.aberta)
    )
    return resultado.scalar_one_or_none()


@router.get("", response_model=MesaPublicaOut)
async def ver_mesa(numero: int, t: str | None = Query(default=None), db: AsyncSession = Depends(get_db)):
    mesa = await mesa_service.exigir_mesa_pelo_token(db, numero, t)

    produtos = (
        await db.execute(
            select(Produto).where(Produto.disponivel.is_(True)).order_by(Produto.categoria, Produto.nome)
        )
    ).scalars()
    comanda = await _comanda_aberta(db, mesa.id)
    pedidos = await pedido_service.listar(db, comanda_id=comanda.id) if comanda else []
    chamado = await chamado_service.chamado_aberto(db, mesa.id)

    return MesaPublicaOut(
        numero=mesa.numero,
        cardapio=[ProdutoPublicoOut(id=p.id, nome=p.nome, categoria=p.categoria, preco=p.preco) for p in produtos],
        comanda=ComandaPublicaOut(id=comanda.id, status=comanda.status) if comanda else None,
        pedidos=pedidos,
        chamado_aberto=chamado is not None,
    )


@router.post("/comanda", response_model=ComandaPublicaOut)
async def abrir_comanda(
    numero: int,
    dados: AbrirComandaPublicaRequest | None = None,
    t: str | None = Query(default=None),
    db: AsyncSession = Depends(get_db),
) -> ComandaPublicaOut:
    await mesa_service.exigir_mesa_pelo_token(db, numero, t)
    origem = (dados or AbrirComandaPublicaRequest()).origem
    comanda = await comanda_service.abrir_por_mesa(db, numero, origem)
    return ComandaPublicaOut(id=comanda.id, status=comanda.status)


@router.post("/chamar-garcom", response_model=ChamadoOut)
async def chamar_garcom(
    numero: int, t: str | None = Query(default=None), db: AsyncSession = Depends(get_db)
) -> ChamadoOut:
    mesa = await mesa_service.exigir_mesa_pelo_token(db, numero, t)
    return await chamado_service.chamar_garcom(db, mesa)


@router.get("/conta", response_model=ContaOut)
async def ver_conta(numero: int, t: str | None = Query(default=None), db: AsyncSession = Depends(get_db)) -> ContaOut:
    mesa = await mesa_service.exigir_mesa_pelo_token(db, numero, t)
    comanda = await _comanda_aberta(db, mesa.id)
    if comanda is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Nenhuma comanda aberta nesta mesa")
    return await comanda_service.calcular_conta(db, comanda, com_taxa=True)
