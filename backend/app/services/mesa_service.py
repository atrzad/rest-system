import secrets

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.mesa import Mesa


async def mesa_pelo_token(db: AsyncSession, numero: int, token: str | None) -> Mesa | None:
    """Mesa ativa cujo token confere, ou None. Compara em tempo constante."""
    if not token:
        return None
    mesa = (await db.execute(select(Mesa).where(Mesa.numero == numero))).scalar_one_or_none()
    if mesa is None or not mesa.ativa:
        return None
    if not secrets.compare_digest(mesa.token.encode(), token.strip().upper().encode()):
        return None
    return mesa


async def exigir_mesa_pelo_token(db: AsyncSession, numero: int, token: str | None) -> Mesa:
    mesa = await mesa_pelo_token(db, numero, token)
    if mesa is None:
        # Mesma resposta para mesa inexistente e token errado: não revela quais mesas existem.
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Mesa não encontrada")
    return mesa
