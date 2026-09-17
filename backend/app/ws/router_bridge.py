import json
import logging

from app.events.bus import CANAL_EVENTOS, get_redis
from app.models.roles import Role
from app.ws.manager import manager

logger = logging.getLogger(__name__)

ROTEAMENTO_POR_TIPO: dict[str, list[Role]] = {
    "comanda_aberta": [Role.salao],
    "garcom_chamado": [Role.salao],
    "pedido_criado": [Role.cozinha],
    "pedido_em_preparo": [Role.salao],
    "pedido_pronto": [Role.salao],
    "pedido_entregue": [Role.salao],
    "pedido_cancelado": [Role.cozinha, Role.salao],
    "comanda_fechada": [Role.salao],
}


async def escutar_eventos() -> None:
    """Consome o canal Redis e faz fan-out para os WebSockets certos por role/mesa."""
    client = get_redis()
    pubsub = client.pubsub()
    await pubsub.subscribe(CANAL_EVENTOS)

    async for mensagem in pubsub.listen():
        if mensagem["type"] != "message":
            continue

        try:
            dados = json.loads(mensagem["data"])
        except (TypeError, ValueError):
            logger.warning("Evento inválido recebido no canal %s: %r", CANAL_EVENTOS, mensagem["data"])
            continue

        roles = ROTEAMENTO_POR_TIPO.get(dados.get("tipo"), [])
        if roles:
            await manager.enviar_para_roles(roles, mensagem["data"])

        mesa_numero = dados.get("mesa_numero")
        if mesa_numero is not None:
            await manager.enviar_para_mesa(mesa_numero, mensagem["data"])
