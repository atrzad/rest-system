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
