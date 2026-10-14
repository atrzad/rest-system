import logging
import uuid
from datetime import datetime, timezone

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.events.bus import publish_event
from app.events.schemas import EventoEnvelope
from app.models.chamado import Chamado
from app.models.comanda import Comanda, ComandaStatus
from app.models.mesa import Mesa
from app.schemas.chamado import ChamadoOut

logger = logging.getLogger(__name__)


def _to_out(chamado: Chamado, mesa_numero: int) -> ChamadoOut:
    return ChamadoOut(
        id=chamado.id,
        mesa_numero=mesa_numero,
        comanda_id=chamado.comanda_id,
        criado_em=chamado.criado_em,
        atendido_em=chamado.atendido_em,
    )


async def chamado_aberto(db: AsyncSession, mesa_id: uuid.UUID) -> Chamado | None:
    resultado = await db.execute(select(Chamado).where(Chamado.mesa_id == mesa_id, Chamado.atendido_em.is_(None)))
    return resultado.scalar_one_or_none()


async def chamar_garcom(db: AsyncSession, mesa: Mesa) -> ChamadoOut:
    """Abre um chamado para a mesa. Se já houver um aberto, devolve ele (o botão é idempotente)."""
    mesa_id, mesa_numero = mesa.id, mesa.numero  # guardados: um rollback expira os objetos
    existente = await chamado_aberto(db, mesa_id)
    if existente is not None:
        return _to_out(existente, mesa_numero)

    comanda_id = (
        await db.execute(
            select(Comanda.id).where(Comanda.mesa_id == mesa_id, Comanda.status == ComandaStatus.aberta)
        )
    ).scalar_one_or_none()
    chamado = Chamado(mesa_id=mesa_id, comanda_id=comanda_id)
    db.add(chamado)
    try:
        await db.commit()
    except IntegrityError:
        # Dois toques ao mesmo tempo: o índice uq_chamado_aberto_por_mesa barrou o segundo.
        await db.rollback()
        existente = await chamado_aberto(db, mesa_id)
        if existente is None:
            raise
        return _to_out(existente, mesa_numero)

    await db.refresh(chamado)
    resultado = _to_out(chamado, mesa_numero)
    await publish_event(
        EventoEnvelope(
            tipo="garcom_chamado",
            mesa_numero=mesa_numero,
            comanda_id=str(comanda_id) if comanda_id else None,
            payload=resultado.model_dump(mode="json"),
        )
    )
    logger.info("Garçom chamado: mesa=%s chamado_id=%s", mesa_numero, chamado.id)
    return resultado


async def listar_abertos(db: AsyncSession) -> list[ChamadoOut]:
    resultado = await db.execute(
        select(Chamado, Mesa.numero)
        .join(Mesa, Chamado.mesa_id == Mesa.id)
        .where(Chamado.atendido_em.is_(None))
        .order_by(Chamado.criado_em)
    )
    return [_to_out(chamado, numero) for chamado, numero in resultado.all()]


async def atender(db: AsyncSession, chamado_id: uuid.UUID, funcionario_id: uuid.UUID) -> ChamadoOut:
    """Marca o chamado como atendido. Se outro garçom já atendeu, só devolve o estado atual."""
    chamado = await db.get(Chamado, chamado_id)
    if chamado is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Chamado não encontrado")
    mesa = await db.get(Mesa, chamado.mesa_id)
    if chamado.atendido_em is not None:
        return _to_out(chamado, mesa.numero)

    chamado.atendido_em = datetime.now(timezone.utc)
    chamado.atendido_por = funcionario_id
    await db.commit()
    await db.refresh(chamado)

    resultado = _to_out(chamado, mesa.numero)
    await publish_event(
        EventoEnvelope(
            tipo="chamado_atendido",
            mesa_numero=mesa.numero,
            comanda_id=str(chamado.comanda_id) if chamado.comanda_id else None,
            payload=resultado.model_dump(mode="json"),
        )
    )
    logger.info("Chamado atendido: mesa=%s chamado_id=%s", mesa.numero, chamado.id)
    return resultado
