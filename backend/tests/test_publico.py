from collections.abc import AsyncIterator

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool
from starlette.testclient import TestClient
from starlette.websockets import WebSocketDisconnect

from app.db.session import get_db
from app.main import app
from app.models.funcionario import Funcionario
from app.models.mesa import Mesa
from app.models.produto import Produto
from tests.conftest import TEST_DATABASE_URL, auth_header


def _url(mesa: Mesa, sufixo: str = "", token: str | None = None) -> str:
    return f"/publico/mesas/{mesa.numero}{sufixo}?t={token if token is not None else mesa.token}"


@pytest.mark.parametrize(
    ("metodo", "sufixo"),
    [("GET", ""), ("POST", "/comanda"), ("POST", "/chamar-garcom"), ("GET", "/conta")],
)
@pytest.mark.parametrize("token", ["ERRADO", ""])
async def test_rotas_publicas_sem_token_valido_retornam_404(
    client: AsyncClient, mesa: Mesa, metodo: str, sufixo: str, token: str
):
    resposta = await client.request(metodo, _url(mesa, sufixo, token))

    assert resposta.status_code == 404
    assert resposta.json()["detail"] == "Mesa não encontrada"


async def test_token_aceita_minusculas_e_espacos(client: AsyncClient, mesa: Mesa):
    resposta = await client.get(_url(mesa, token=f" {mesa.token.lower()} "))

    assert resposta.status_code == 200


async def test_cliente_abre_comanda_e_ve_cardapio_e_pedidos(
    client: AsyncClient, salao: Funcionario, mesa: Mesa, produto: Produto
):
    comanda = await client.post(_url(mesa, "/comanda"), json={"origem": "cliente_manual"})
    assert comanda.status_code == 200
    comanda_id = comanda.json()["id"]
    await client.post(
        "/pedidos",
        headers=auth_header(salao),
        json={"comanda_id": comanda_id, "itens": [{"produto_id": str(produto.id), "quantidade": 3}]},
    )

    visao = (await client.get(_url(mesa))).json()
    conta = (await client.get(_url(mesa, "/conta"))).json()

    assert visao["numero"] == mesa.numero
    assert visao["comanda"]["id"] == comanda_id
    assert [p["nome"] for p in visao["cardapio"]] == [produto.nome]
    assert visao["pedidos"][0]["itens"][0]["quantidade"] == 3
    assert visao["chamado_aberto"] is False
    assert conta["subtotal"] == "30.00"
    assert conta["total"] == "33.00"

    comandas = (await client.get("/comandas", headers=auth_header(salao))).json()
    assert comandas[0]["aberta_por"] == "cliente_manual"


async def test_conta_sem_comanda_aberta_retorna_404(client: AsyncClient, mesa: Mesa):
    resposta = await client.get(_url(mesa, "/conta"))

    assert resposta.status_code == 404
    assert "comanda" in resposta.json()["detail"]


async def test_chamar_garcom_duas_vezes_gera_um_chamado_e_atender_limpa(
    client: AsyncClient, salao: Funcionario, mesa: Mesa
):
    primeiro = await client.post(_url(mesa, "/chamar-garcom"))
    segundo = await client.post(_url(mesa, "/chamar-garcom"))

    assert primeiro.status_code == segundo.status_code == 200
    assert primeiro.json()["id"] == segundo.json()["id"]
    abertos = (await client.get("/chamados", headers=auth_header(salao))).json()
    assert [c["mesa_numero"] for c in abertos] == [mesa.numero]
    assert (await client.get(_url(mesa))).json()["chamado_aberto"] is True

    atendido = await client.post(f"/chamados/{primeiro.json()['id']}/atender", headers=auth_header(salao))
    de_novo = await client.post(f"/chamados/{primeiro.json()['id']}/atender", headers=auth_header(salao))

    assert atendido.status_code == de_novo.status_code == 200
    assert atendido.json()["atendido_em"] is not None
    assert (await client.get("/chamados", headers=auth_header(salao))).json() == []
    assert (await client.get(_url(mesa))).json()["chamado_aberto"] is False

    novo = await client.post(_url(mesa, "/chamar-garcom"))
    assert novo.json()["id"] != primeiro.json()["id"]


async def test_chamados_exigem_salao_ou_admin(client: AsyncClient, cozinha: Funcionario):
    assert (await client.get("/chamados")).status_code == 401
    assert (await client.get("/chamados", headers=auth_header(cozinha))).status_code == 403


async def test_token_da_mesa_so_aparece_para_admin(
    client: AsyncClient, admin: Funcionario, salao: Funcionario, mesa: Mesa
):
    do_admin = (await client.get("/mesas", headers=auth_header(admin))).json()[0]
    do_salao = (await client.get("/mesas", headers=auth_header(salao))).json()[0]

    assert do_admin["token"] == mesa.token
    assert do_admin["url_qr"].endswith(f"/mesa/{mesa.numero}?t={mesa.token}")
    assert do_salao["token"] is None
    assert do_salao["url_qr"] is None


async def test_regenerar_token_invalida_o_qr_antigo(client: AsyncClient, admin: Funcionario, mesa: Mesa):
    resposta = await client.post(f"/mesas/{mesa.id}/regenerar-token", headers=auth_header(admin))

    novo_token = resposta.json()["token"]
    assert novo_token != mesa.token
    assert (await client.get(_url(mesa))).status_code == 404
    assert (await client.get(_url(mesa, token=novo_token))).status_code == 200


async def test_salao_nao_regenera_token(client: AsyncClient, salao: Funcionario, mesa: Mesa):
    resposta = await client.post(f"/mesas/{mesa.id}/regenerar-token", headers=auth_header(salao))

    assert resposta.status_code == 403


async def test_qrcode_png(client: AsyncClient, admin: Funcionario, mesa: Mesa):
    resposta = await client.get(f"/mesas/{mesa.id}/qrcode.png", headers=auth_header(admin))

    assert resposta.status_code == 200
    assert resposta.headers["content-type"] == "image/png"
    assert resposta.content.startswith(b"\x89PNG")


@pytest.fixture
def ws_client() -> TestClient:
    """TestClient roda o app em outra thread/loop; por isso uma engine sem pool, criada lá dentro."""

    async def override_get_db() -> AsyncIterator[AsyncSession]:
        engine = create_async_engine(TEST_DATABASE_URL, poolclass=NullPool)
        async with async_sessionmaker(engine, expire_on_commit=False)() as session:
            yield session
        await engine.dispose()

    app.dependency_overrides[get_db] = override_get_db
    yield TestClient(app)
    app.dependency_overrides.clear()


def test_ws_da_mesa_com_token_certo_conecta(ws_client: TestClient, mesa: Mesa):
    with ws_client.websocket_connect(f"/ws?mesa={mesa.numero}&t={mesa.token}") as ws:
        ws.close()


@pytest.mark.parametrize("token", ["ERRADO", None])
def test_ws_da_mesa_com_token_errado_e_recusado(ws_client: TestClient, mesa: Mesa, token: str | None):
    query = f"/ws?mesa={mesa.numero}" + (f"&t={token}" if token else "")
    with pytest.raises(WebSocketDisconnect) as erro:
        with ws_client.websocket_connect(query) as ws:
            ws.receive_text()

    assert erro.value.code == 1008
