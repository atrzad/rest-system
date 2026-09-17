import uuid
from datetime import datetime, timezone

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.comanda import Comanda, ComandaStatus, OrigemAbertura
from app.models.mesa import Mesa


async def abrir_por_mesa(db: AsyncSession, numero_mesa: int, origem: OrigemAbertura) -> Comanda:
    mesa = (await db.execute(select(Mesa).where(Mesa.numero == numero_mesa))).scalar_one_or_none()
    if mesa is None or not mesa.ativa:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Mesa não encontrada ou inativa")

    aberta = (
        await db.execute(
            select(Comanda).where(Comanda.mesa_id == mesa.id, Comanda.status == ComandaStatus.aberta)
        )
    ).scalar_one_or_none()
    if aberta is not None:
        return aberta

    comanda = Comanda(mesa_id=mesa.id, aberta_por=origem)
    db.add(comanda)
    await db.commit()
    await db.refresh(comanda)
    return comanda


async def fechar(db: AsyncSession, comanda_id: uuid.UUID) -> Comanda:
    comanda = await db.get(Comanda, comanda_id)
    if comanda is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Comanda não encontrada")
    if comanda.status == ComandaStatus.fechada:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Comanda já está fechada")

    comanda.status = ComandaStatus.fechada
    comanda.fechada_em = datetime.now(timezone.utc)
    await db.commit()
    await db.refresh(comanda)
    return comanda
