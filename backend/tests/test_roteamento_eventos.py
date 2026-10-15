import json

import pytest

from app.models.roles import Role
from app.ws import router_bridge


class ManagerFalso:
    def __init__(self) -> None:
        self.para_roles: list[list[Role]] = []
        self.para_mesa: list[int] = []

    async def enviar_para_roles(self, roles: list[Role], mensagem: str) -> None:
        self.para_roles.append(roles)

    async def enviar_para_mesa(self, mesa_numero: int, mensagem: str) -> None:
        self.para_mesa.append(mesa_numero)


@pytest.mark.parametrize("tipo", ["pedido_criado", "pedido_em_preparo", "pedido_pronto", "pedido_entregue", "pedido_cancelado"])
async def test_kds_recebe_todas_as_mudancas_de_pedido(monkeypatch, tipo):
    """Sem isso, o pedido entregue pelo salão ficava preso na coluna "Pronto" do KDS."""
    falso = ManagerFalso()
    monkeypatch.setattr(router_bridge, "manager", falso)

    await router_bridge._rotear(json.dumps({"tipo": tipo, "mesa_numero": 3}))

    assert Role.cozinha in falso.para_roles[0]
    assert falso.para_mesa == [3]


async def test_chamados_nao_vao_para_a_cozinha(monkeypatch):
    falso = ManagerFalso()
    monkeypatch.setattr(router_bridge, "manager", falso)

    await router_bridge._rotear(json.dumps({"tipo": "garcom_chamado", "mesa_numero": 3}))

    assert falso.para_roles == [[Role.salao]]
