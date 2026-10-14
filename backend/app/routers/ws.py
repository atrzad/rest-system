from fastapi import APIRouter, Depends, Query, WebSocket, WebSocketDisconnect, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.security import decodificar_access_token
from app.db.session import get_db
from app.models.roles import Role
from app.services import mesa_service
from app.ws.manager import manager

router = APIRouter()


@router.websocket("/ws")
async def websocket_endpoint(
    websocket: WebSocket,
    token: str | None = Query(default=None),
    mesa: int | None = Query(default=None),
    t: str | None = Query(default=None),
    db: AsyncSession = Depends(get_db),
) -> None:
    if token is not None:
        try:
            payload = decodificar_access_token(token)
            role = Role(payload["role"])
        except (ValueError, KeyError):
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
            return
        await db.close()  # devolve a conexão ao pool: a sessão não é usada durante o WebSocket
        await manager.conectar_staff(websocket, role)
    elif mesa is not None:
        # Cliente da mesa: precisa do mesmo token do QR, senão qualquer um acompanharia qualquer mesa.
        mesa_valida = await mesa_service.mesa_pelo_token(db, mesa, t)
        await db.close()
        if mesa_valida is None:
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
            return
        await manager.conectar_mesa(websocket, mesa)
    else:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return

    try:
        while True:
            # Não esperamos mensagens do cliente; só mantemos a conexão viva.
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.desconectar(websocket)
