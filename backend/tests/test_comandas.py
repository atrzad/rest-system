from httpx import AsyncClient

from app.models.funcionario import Funcionario
from app.models.mesa import Mesa
from tests.conftest import abrir_comanda, auth_header, header_staff


async def test_abrir_comanda_pelo_garcom(client: AsyncClient, salao: Funcionario, mesa: Mesa):
    resposta = await client.post(
        "/comandas/abrir-por-mesa", headers=auth_header(salao), json={"numero_mesa": mesa.numero}
    )

    assert resposta.status_code == 200
    corpo = resposta.json()
    assert corpo["status"] == "aberta"
    assert corpo["mesa_numero"] == mesa.numero
    assert corpo["aberta_por"] == "garcom"


async def test_abrir_comanda_sem_login_retorna_401(client: AsyncClient, mesa: Mesa):
    resposta = await client.post("/comandas/abrir-por-mesa", json={"numero_mesa": mesa.numero})

    assert resposta.status_code == 401


async def test_cozinha_nao_abre_comanda(client: AsyncClient, cozinha: Funcionario, mesa: Mesa):
    resposta = await client.post(
        "/comandas/abrir-por-mesa", headers=auth_header(cozinha), json={"numero_mesa": mesa.numero}
    )

    assert resposta.status_code == 403


async def test_abrir_comanda_reaproveita_comanda_ja_aberta(client: AsyncClient, mesa: Mesa):
    primeira = await abrir_comanda(client, mesa.numero)
    segunda = await abrir_comanda(client, mesa.numero)

    assert primeira == segunda


async def test_abrir_comanda_mesa_inexistente_retorna_404(client: AsyncClient):
    resposta = await client.post("/comandas/abrir-por-mesa", headers=header_staff(), json={"numero_mesa": 999})

    assert resposta.status_code == 404


async def test_listar_comandas_sem_token_retorna_401(client: AsyncClient):
    resposta = await client.get("/comandas")

    assert resposta.status_code == 401


async def test_fechar_comanda_e_fechar_de_novo_falha(client: AsyncClient, salao: Funcionario, mesa: Mesa):
    comanda_id = await abrir_comanda(client, mesa.numero)

    fechamento = await client.post(f"/comandas/{comanda_id}/fechar", headers=auth_header(salao))
    assert fechamento.status_code == 200
    assert fechamento.json()["status"] == "fechada"

    segunda_tentativa = await client.post(f"/comandas/{comanda_id}/fechar", headers=auth_header(salao))
    assert segunda_tentativa.status_code == 400
