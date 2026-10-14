import logging
import uuid

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.events.bus import publish_event
from app.events.schemas import EventoEnvelope
from app.models.comanda import Comanda, ComandaStatus
from app.models.mesa import Mesa
from app.models.pedido import Pedido, PedidoStatus
from app.models.pedido_item import PedidoItem
from app.models.produto import Produto
from app.models.roles import Role
from app.schemas.pedido import PedidoItemCreate, PedidoItemOut, PedidoOut

logger = logging.getLogger(__name__)

TRANSICOES_VALIDAS: dict[PedidoStatus, set[PedidoStatus]] = {
    PedidoStatus.recebido: {PedidoStatus.em_preparo, PedidoStatus.cancelado},
    PedidoStatus.em_preparo: {PedidoStatus.pronto, PedidoStatus.cancelado},
    PedidoStatus.pronto: {PedidoStatus.entregue},
    PedidoStatus.entregue: set(),
    PedidoStatus.cancelado: set(),
}

# Quem pode fazer cada transição. Admin pode tudo que TRANSICOES_VALIDAS permite.
TRANSICOES_POR_ROLE: dict[Role, set[tuple[PedidoStatus, PedidoStatus]]] = {
    Role.cozinha: {
        (PedidoStatus.recebido, PedidoStatus.em_preparo),
        (PedidoStatus.em_preparo, PedidoStatus.pronto),
        (PedidoStatus.recebido, PedidoStatus.cancelado),
        (PedidoStatus.em_preparo, PedidoStatus.cancelado),
    },
    Role.salao: {
        (PedidoStatus.pronto, PedidoStatus.entregue),
        (PedidoStatus.recebido, PedidoStatus.cancelado),
    },
}

EVENTO_POR_STATUS: dict[PedidoStatus, str] = {
    PedidoStatus.em_preparo: "pedido_em_preparo",
    PedidoStatus.pronto: "pedido_pronto",
    PedidoStatus.entregue: "pedido_entregue",
    PedidoStatus.cancelado: "pedido_cancelado",
}


async def _mesa_numero_da_comanda(db: AsyncSession, comanda_id: uuid.UUID) -> int:
    resultado = await db.execute(
        select(Mesa.numero).join(Comanda, Comanda.mesa_id == Mesa.id).where(Comanda.id == comanda_id)
    )
    return resultado.scalar_one()


async def _itens_out(db: AsyncSession, pedido_id: uuid.UUID) -> list[PedidoItemOut]:
    resultado = await db.execute(
        select(PedidoItem, Produto.nome)
        .join(Produto, PedidoItem.produto_id == Produto.id)
        .where(PedidoItem.pedido_id == pedido_id)
    )
    return [
        PedidoItemOut(
            id=item.id,
            produto_id=item.produto_id,
            produto_nome=nome,
            quantidade=item.quantidade,
            preco_unitario=item.preco_unitario,
            observacao=item.observacao,
        )
        for item, nome in resultado.all()
    ]


async def _to_out(db: AsyncSession, pedido: Pedido) -> PedidoOut:
    mesa_numero = await _mesa_numero_da_comanda(db, pedido.comanda_id)
    itens = await _itens_out(db, pedido.id)
    return PedidoOut(
        id=pedido.id,
        comanda_id=pedido.comanda_id,
        mesa_numero=mesa_numero,
        status=pedido.status,
        criado_em=pedido.criado_em,
        atualizado_em=pedido.atualizado_em,
        itens=itens,
    )


async def criar_pedido(db: AsyncSession, comanda_id: uuid.UUID, itens: list[PedidoItemCreate]) -> PedidoOut:
    comanda = await db.get(Comanda, comanda_id)
    if comanda is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Comanda não encontrada")
    if comanda.status != ComandaStatus.aberta:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Comanda não está aberta")

    pedido = Pedido(comanda_id=comanda_id)
    db.add(pedido)
    await db.flush()

    for item in itens:
        produto = await db.get(Produto, item.produto_id)
        if produto is None:
            raise HTTPException(status.HTTP_404_NOT_FOUND, f"Produto {item.produto_id} não encontrado")
        if not produto.disponivel:
            raise HTTPException(status.HTTP_400_BAD_REQUEST, f"Produto '{produto.nome}' não está disponível")
        db.add(
            PedidoItem(
                pedido_id=pedido.id,
                produto_id=produto.id,
                quantidade=item.quantidade,
                preco_unitario=produto.preco,
                observacao=item.observacao,
            )
        )

    await db.commit()
    await db.refresh(pedido)

    resultado = await _to_out(db, pedido)

    mesa = await db.get(Mesa, comanda.mesa_id)
    await publish_event(
        EventoEnvelope(
            tipo="pedido_criado",
            mesa_numero=mesa.numero,
            comanda_id=str(comanda_id),
            payload=resultado.model_dump(mode="json"),
        )
    )
    logger.info("Pedido criado: pedido_id=%s comanda_id=%s mesa=%s", pedido.id, comanda_id, mesa.numero)

    return resultado


async def listar(
    db: AsyncSession,
    status_filtro: PedidoStatus | None = None,
    comanda_id: uuid.UUID | None = None,
) -> list[PedidoOut]:
    query = (
        select(Pedido, Mesa.numero)
        .join(Comanda, Pedido.comanda_id == Comanda.id)
        .join(Mesa, Comanda.mesa_id == Mesa.id)
        .order_by(Pedido.criado_em)
    )
    if status_filtro is not None:
        query = query.where(Pedido.status == status_filtro)
    if comanda_id is not None:
        query = query.where(Pedido.comanda_id == comanda_id)

    linhas = (await db.execute(query)).all()
    if not linhas:
        return []

    # Uma query só para os itens de todos os pedidos (evita N+1).
    itens_por_pedido: dict[uuid.UUID, list[PedidoItemOut]] = {pedido.id: [] for pedido, _ in linhas}
    resultado_itens = await db.execute(
        select(PedidoItem, Produto.nome)
        .join(Produto, PedidoItem.produto_id == Produto.id)
        .where(PedidoItem.pedido_id.in_(itens_por_pedido.keys()))
    )
    for item, nome in resultado_itens.all():
        itens_por_pedido[item.pedido_id].append(
            PedidoItemOut(
                id=item.id,
                produto_id=item.produto_id,
                produto_nome=nome,
                quantidade=item.quantidade,
                preco_unitario=item.preco_unitario,
                observacao=item.observacao,
            )
        )

    return [
        PedidoOut(
            id=pedido.id,
            comanda_id=pedido.comanda_id,
            mesa_numero=mesa_numero,
            status=pedido.status,
            criado_em=pedido.criado_em,
            atualizado_em=pedido.atualizado_em,
            itens=itens_por_pedido[pedido.id],
        )
        for pedido, mesa_numero in linhas
    ]


async def atualizar_status(
    db: AsyncSession, pedido_id: uuid.UUID, novo_status: PedidoStatus, role: Role
) -> PedidoOut:
    pedido = await db.get(Pedido, pedido_id)
    if pedido is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Pedido não encontrado")

    if novo_status not in TRANSICOES_VALIDAS[pedido.status]:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            f"Transição inválida de '{pedido.status.value}' para '{novo_status.value}'",
        )
    if role != Role.admin and (pedido.status, novo_status) not in TRANSICOES_POR_ROLE.get(role, set()):
        raise HTTPException(
            status.HTTP_403_FORBIDDEN,
            f"O perfil '{role.value}' não pode mudar um pedido de '{pedido.status.value}' para '{novo_status.value}'",
        )

    pedido.status = novo_status
    await db.commit()
    await db.refresh(pedido)

    resultado = await _to_out(db, pedido)

    comanda = await db.get(Comanda, pedido.comanda_id)
    mesa = await db.get(Mesa, comanda.mesa_id)
    evento_tipo = EVENTO_POR_STATUS.get(novo_status)
    if evento_tipo:
        await publish_event(
            EventoEnvelope(
                tipo=evento_tipo,
                mesa_numero=mesa.numero,
                comanda_id=str(pedido.comanda_id),
                payload=resultado.model_dump(mode="json"),
            )
        )

    logger.info("Pedido %s mudou de status para %s", pedido.id, novo_status.value)
    return resultado
