import logging
import uuid
from datetime import datetime, timezone
from decimal import ROUND_HALF_UP, Decimal

from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.events.bus import publish_event
from app.events.schemas import EventoEnvelope
from app.models.comanda import Comanda, ComandaStatus, OrigemAbertura
from app.models.mesa import Mesa
from app.models.pedido import Pedido, PedidoStatus
from app.models.pedido_item import PedidoItem
from app.models.produto import Produto
from app.schemas.comanda import ContaItemOut, ContaOut
from app.services import venda_evento_service

logger = logging.getLogger(__name__)

TAXA_SERVICO = Decimal("0.10")
CENTAVOS = Decimal("0.01")
STATUS_PENDENTES = (PedidoStatus.recebido, PedidoStatus.em_preparo, PedidoStatus.pronto)


async def _comanda_aberta_da_mesa(db: AsyncSession, mesa_id: uuid.UUID) -> Comanda | None:
    resultado = await db.execute(
        select(Comanda).where(Comanda.mesa_id == mesa_id, Comanda.status == ComandaStatus.aberta)
    )
    return resultado.scalar_one_or_none()


async def abrir_por_mesa(db: AsyncSession, numero_mesa: int, origem: OrigemAbertura) -> Comanda:
    mesa = (await db.execute(select(Mesa).where(Mesa.numero == numero_mesa))).scalar_one_or_none()
    if mesa is None or not mesa.ativa:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Mesa não encontrada ou inativa")

    mesa_id = mesa.id  # guardado antes do commit: um rollback expira os objetos da sessão
    aberta = await _comanda_aberta_da_mesa(db, mesa_id)
    if aberta is not None:
        return aberta

    comanda = Comanda(mesa_id=mesa_id, aberta_por=origem)
    db.add(comanda)
    try:
        await db.commit()
    except IntegrityError:
        # Outra requisição abriu a comanda desta mesa ao mesmo tempo (índice uq_comanda_aberta_por_mesa).
        await db.rollback()
        aberta = await _comanda_aberta_da_mesa(db, mesa_id)
        if aberta is None:
            raise
        return aberta

    await db.refresh(comanda)
    await publish_event(
        EventoEnvelope(
            tipo="comanda_aberta",
            mesa_numero=numero_mesa,
            comanda_id=str(comanda.id),
            payload={"origem": origem.value},
        )
    )
    logger.info("Comanda aberta: mesa=%s origem=%s comanda_id=%s", numero_mesa, origem.value, comanda.id)
    return comanda


async def calcular_conta(db: AsyncSession, comanda: Comanda, com_taxa: bool) -> ContaOut:
    """Soma os itens dos pedidos não cancelados, agrupados por produto e preço."""
    valor = func.sum(PedidoItem.quantidade * PedidoItem.preco_unitario)
    resultado = await db.execute(
        select(
            PedidoItem.produto_id,
            Produto.nome,
            PedidoItem.preco_unitario,
            func.sum(PedidoItem.quantidade),
            valor,
        )
        .join(Pedido, PedidoItem.pedido_id == Pedido.id)
        .join(Produto, PedidoItem.produto_id == Produto.id)
        .where(Pedido.comanda_id == comanda.id, Pedido.status != PedidoStatus.cancelado)
        .group_by(PedidoItem.produto_id, Produto.nome, PedidoItem.preco_unitario)
        .order_by(Produto.nome)
    )
    itens = [
        ContaItemOut(
            produto_id=produto_id,
            produto_nome=nome,
            preco_unitario=preco,
            quantidade=quantidade,
            valor=valor_item,
        )
        for produto_id, nome, preco, quantidade, valor_item in resultado.all()
    ]

    pendentes = (
        await db.execute(
            select(func.count())
            .select_from(Pedido)
            .where(Pedido.comanda_id == comanda.id, Pedido.status.in_(STATUS_PENDENTES))
        )
    ).scalar_one()

    subtotal = sum((item.valor for item in itens), Decimal("0")).quantize(CENTAVOS)
    taxa = (subtotal * TAXA_SERVICO).quantize(CENTAVOS, rounding=ROUND_HALF_UP) if com_taxa else Decimal("0.00")
    mesa = await db.get(Mesa, comanda.mesa_id)
    return ContaOut(
        comanda_id=comanda.id,
        mesa_numero=mesa.numero,
        itens=itens,
        subtotal=subtotal,
        taxa_servico=taxa,
        total=subtotal + taxa,
        pedidos_pendentes=pendentes,
    )


async def obter(db: AsyncSession, comanda_id: uuid.UUID) -> Comanda:
    comanda = await db.get(Comanda, comanda_id)
    if comanda is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Comanda não encontrada")
    return comanda


async def fechar(db: AsyncSession, comanda_id: uuid.UUID, com_taxa: bool) -> Comanda:
    comanda = await obter(db, comanda_id)
    if comanda.status == ComandaStatus.fechada:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Comanda já está fechada")

    conta = await calcular_conta(db, comanda, com_taxa)
    if conta.pedidos_pendentes:
        raise HTTPException(
            status.HTTP_409_CONFLICT,
            f"Há {conta.pedidos_pendentes} pedido(s) pendente(s): marque como entregue ou cancele antes de fechar",
        )

    comanda.status = ComandaStatus.fechada
    comanda.fechada_em = datetime.now(timezone.utc)
    comanda.subtotal = conta.subtotal
    comanda.taxa_servico = conta.taxa_servico
    comanda.total = conta.total
    venda_evento_service.registrar(
        db,
        "comanda_fechada",
        comanda_id=comanda.id,
        valor=conta.total,
        payload={"subtotal": str(conta.subtotal), "taxa_servico": str(conta.taxa_servico), "mesa": conta.mesa_numero},
    )
    await db.commit()
    await db.refresh(comanda)

    await publish_event(
        EventoEnvelope(
            tipo="comanda_fechada",
            mesa_numero=conta.mesa_numero,
            comanda_id=str(comanda.id),
            payload={
                "subtotal": str(conta.subtotal),
                "taxa_servico": str(conta.taxa_servico),
                "total": str(conta.total),
            },
        )
    )
    logger.info("Comanda fechada: comanda_id=%s total=%s", comanda.id, comanda.total)
    return comanda
