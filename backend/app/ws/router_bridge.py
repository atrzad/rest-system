import asyncio
import contextlib
import json
import logging

from redis.exceptions import ConnectionError as RedisConnectionError

from app.events.bus import CANAL_EVENTOS, get_redis
from app.models.roles import Role
from app.ws.manager import manager

logger = logging.getLogger(__name__)

ESPERA_INICIAL = 1
ESPERA_MAXIMA = 30

ROTEAMENTO_POR_TIPO: dict[str, list[Role]] = {
    "comanda_aberta": [Role.salao],
    "garcom_chamado": [Role.salao],
    "chamado_atendido": [Role.salao],
    "pedido_criado": [Role.cozinha],
    "pedido_em_preparo": [Role.salao],
    "pedido_pronto": [Role.salao],
    "pedido_entregue": [Role.salao],
    "pedido_cancelado": [Role.cozinha, Role.salao],
    "comanda_fechada": [Role.salao, Role.admin],
}


async def _rotear(dados_brutos: str) -> None:
    try:
        dados = json.loads(dados_brutos)
    except (TypeError, ValueError):
        logger.warning("Evento inválido recebido no canal %s: %r", CANAL_EVENTOS, dados_brutos)
        return

    roles = ROTEAMENTO_POR_TIPO.get(dados.get("tipo"), [])
    if roles:
        await manager.enviar_para_roles(roles, dados_brutos)

    mesa_numero = dados.get("mesa_numero")
    if mesa_numero is not None:
        await manager.enviar_para_mesa(mesa_numero, dados_brutos)


async def escutar_eventos() -> None:
    """Consome o canal Redis e faz fan-out para os WebSockets certos por role/mesa.

    Se a conexão com o Redis cair, tenta de novo com espera crescente (1s, 2s, 4s... até 30s)
    em vez de deixar a task morrer e o tempo real parar sem aviso.
    """
    espera = ESPERA_INICIAL
    while True:
        pubsub = get_redis().pubsub()
        try:
            await pubsub.subscribe(CANAL_EVENTOS)
            if espera > ESPERA_INICIAL:
                logger.warning("Reconectado ao Redis; eventos em tempo real voltaram")
            espera = ESPERA_INICIAL

            async for mensagem in pubsub.listen():
                if mensagem["type"] == "message":
                    await _rotear(mensagem["data"])
        except asyncio.CancelledError:
            raise
        except RedisConnectionError as exc:
            logger.warning("Conexão com o Redis perdida (%s); tentando de novo em %ss", exc, espera)
        except Exception:
            logger.exception("Erro inesperado no listener de eventos; reiniciando em %ss", espera)
        finally:
            with contextlib.suppress(Exception):
                await pubsub.aclose()

        await asyncio.sleep(espera)
        espera = min(espera * 2, ESPERA_MAXIMA)
