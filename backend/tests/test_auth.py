from httpx import AsyncClient

from app.models.funcionario import Funcionario
from tests.conftest import SENHA_PADRAO, auth_header


async def test_login_com_credenciais_validas_retorna_token(client: AsyncClient, admin: Funcionario):
    resposta = await client.post("/auth/login", json={"email": admin.email, "senha": SENHA_PADRAO})

    assert resposta.status_code == 200
    corpo = resposta.json()
    assert corpo["role"] == "admin"
    assert corpo["access_token"]


async def test_login_com_senha_errada_retorna_401(client: AsyncClient, admin: Funcionario):
    resposta = await client.post("/auth/login", json={"email": admin.email, "senha": "senha-errada"})

    assert resposta.status_code == 401


async def test_login_com_email_inexistente_retorna_401(client: AsyncClient):
    resposta = await client.post("/auth/login", json={"email": "ninguem@teste.com", "senha": SENHA_PADRAO})

    assert resposta.status_code == 401


async def test_me_sem_token_retorna_401(client: AsyncClient):
    resposta = await client.get("/auth/me")

    assert resposta.status_code == 401


async def test_me_com_token_valido_retorna_dados_do_usuario(client: AsyncClient, salao: Funcionario):
    resposta = await client.get("/auth/me", headers=auth_header(salao))

    assert resposta.status_code == 200
    assert resposta.json()["role"] == "salao"
    assert resposta.json()["email"] == salao.email


async def test_login_bloqueia_depois_de_5_senhas_erradas(client: AsyncClient, admin: Funcionario):
    for _ in range(5):
        errada = await client.post("/auth/login", json={"email": admin.email, "senha": "errada!!"})
        assert errada.status_code == 401

    bloqueada = await client.post("/auth/login", json={"email": admin.email, "senha": SENHA_PADRAO})

    assert bloqueada.status_code == 429
    assert "Muitas tentativas" in bloqueada.json()["detail"]


async def test_limite_e_por_email_e_zera_com_login_certo(
    client: AsyncClient, admin: Funcionario, salao: Funcionario
):
    for _ in range(4):
        await client.post("/auth/login", json={"email": admin.email, "senha": "errada!!"})

    assert (await client.post("/auth/login", json={"email": salao.email, "senha": SENHA_PADRAO})).status_code == 200
    assert (await client.post("/auth/login", json={"email": admin.email, "senha": SENHA_PADRAO})).status_code == 200
    # Login certo zerou o contador: mais 4 erradas ainda não bloqueiam.
    for _ in range(4):
        await client.post("/auth/login", json={"email": admin.email, "senha": "errada!!"})
    assert (await client.post("/auth/login", json={"email": admin.email, "senha": SENHA_PADRAO})).status_code == 200
