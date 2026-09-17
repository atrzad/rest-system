from httpx import AsyncClient

from app.models.funcionario import Funcionario
from app.models.mesa import Mesa
from tests.conftest import auth_header


async def test_abrir_comanda_por_mesa_sem_autenticacao(client: AsyncClient, mesa: Mesa):
    resposta = await client.post(
        "/comandas/abrir-por-mesa", json={"numero_mesa": mesa.numero, "origem": "cliente_qr"}
    )

    assert resposta.status_code == 200
    corpo = resposta.json()
    assert corpo["status"] == "aberta"
    assert corpo["mesa_numero"] == mesa.numero


async def test_abrir_comanda_reaproveita_comanda_ja_aberta(client: AsyncClient, mesa: Mesa):
    primeira = await client.post("/comandas/abrir-por-mesa", json={"numero_mesa": mesa.numero, "origem": "garcom"})
    segunda = await client.post(
        "/comandas/abrir-por-mesa", json={"numero_mesa": mesa.numero, "origem": "cliente_manual"}
    )

    assert primeira.json()["id"] == segunda.json()["id"]


async def test_abrir_comanda_mesa_inexistente_retorna_404(client: AsyncClient):
    resposta = await client.post("/comandas/abrir-por-mesa", json={"numero_mesa": 999, "origem": "garcom"})

    assert resposta.status_code == 404


async def test_listar_comandas_sem_token_retorna_401(client: AsyncClient):
    resposta = await client.get("/comandas")

    assert resposta.status_code == 401


async def test_fechar_comanda_e_fechar_de_novo_falha(client: AsyncClient, salao: Funcionario, mesa: Mesa):
    abertura = await client.post("/comandas/abrir-por-mesa", json={"numero_mesa": mesa.numero, "origem": "garcom"})
    comanda_id = abertura.json()["id"]

    fechamento = await client.post(f"/comandas/{comanda_id}/fechar", headers=auth_header(salao))
    assert fechamento.status_code == 200
    assert fechamento.json()["status"] == "fechada"

    segunda_tentativa = await client.post(f"/comandas/{comanda_id}/fechar", headers=auth_header(salao))
    assert segunda_tentativa.status_code == 400
