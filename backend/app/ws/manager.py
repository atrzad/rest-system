from collections import defaultdict

from fastapi import WebSocket

from app.models.roles import Role


class ConnectionManager:
    def __init__(self) -> None:
        self._por_role: dict[Role, set[WebSocket]] = defaultdict(set)
        self._por_mesa: dict[int, set[WebSocket]] = defaultdict(set)

    async def conectar_staff(self, websocket: WebSocket, role: Role) -> None:
        await websocket.accept()
        self._por_role[role].add(websocket)

    async def conectar_mesa(self, websocket: WebSocket, mesa_numero: int) -> None:
        await websocket.accept()
        self._por_mesa[mesa_numero].add(websocket)

    def desconectar(self, websocket: WebSocket) -> None:
        for conexoes in self._por_role.values():
            conexoes.discard(websocket)
        for conexoes in self._por_mesa.values():
            conexoes.discard(websocket)

    async def enviar_para_roles(self, roles: list[Role], mensagem: str) -> None:
        alvo: set[WebSocket] = set()
        for role in roles:
            alvo |= self._por_role.get(role, set())
        await self._enviar(alvo, mensagem)

    async def enviar_para_mesa(self, mesa_numero: int, mensagem: str) -> None:
        await self._enviar(self._por_mesa.get(mesa_numero, set()), mensagem)

    async def _enviar(self, conexoes: set[WebSocket], mensagem: str) -> None:
        mortas = []
        for websocket in conexoes:
            try:
                await websocket.send_text(mensagem)
            except Exception:
                mortas.append(websocket)
        for websocket in mortas:
            self.desconectar(websocket)


manager = ConnectionManager()
