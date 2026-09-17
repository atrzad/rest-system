from fastapi import APIRouter, Query, WebSocket, WebSocketDisconnect, status

from app.auth.security import decodificar_access_token
from app.models.roles import Role
from app.ws.manager import manager

router = APIRouter()


@router.websocket("/ws")
async def websocket_endpoint(
    websocket: WebSocket,
    token: str | None = Query(default=None),
    mesa: int | None = Query(default=None),
) -> None:
    if token is not None:
        try:
            payload = decodificar_access_token(token)
            role = Role(payload["role"])
        except (ValueError, KeyError):
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
            return
        await manager.conectar_staff(websocket, role)
    elif mesa is not None:
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
