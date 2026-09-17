from httpx import AsyncClient

from app.models.funcionario import Funcionario
from tests.conftest import auth_header


async def test_admin_pode_listar_funcionarios(client: AsyncClient, admin: Funcionario, salao: Funcionario):
    resposta = await client.get("/funcionarios", headers=auth_header(admin))

    assert resposta.status_code == 200
    emails = {f["email"] for f in resposta.json()}
    assert admin.email in emails
    assert salao.email in emails


async def test_salao_nao_pode_listar_funcionarios(client: AsyncClient, salao: Funcionario):
    resposta = await client.get("/funcionarios", headers=auth_header(salao))

    assert resposta.status_code == 403


async def test_admin_cria_funcionario(client: AsyncClient, admin: Funcionario):
    resposta = await client.post(
        "/funcionarios",
        headers=auth_header(admin),
        json={"nome": "Novo", "email": "novo@teste.com", "senha": "Senha123!", "role": "cozinha"},
    )

    assert resposta.status_code == 201
    assert resposta.json()["role"] == "cozinha"


async def test_criar_funcionario_com_email_duplicado_retorna_409(
    client: AsyncClient, admin: Funcionario, salao: Funcionario
):
    resposta = await client.post(
        "/funcionarios",
        headers=auth_header(admin),
        json={"nome": "Duplicado", "email": salao.email, "senha": "Senha123!", "role": "salao"},
    )

    assert resposta.status_code == 409


async def test_admin_nao_pode_se_autodesativar(client: AsyncClient, admin: Funcionario):
    resposta = await client.patch(
        f"/funcionarios/{admin.id}",
        headers=auth_header(admin),
        json={"ativo": False},
    )

    assert resposta.status_code == 400


async def test_admin_pode_desativar_outro_funcionario(client: AsyncClient, admin: Funcionario, cozinha: Funcionario):
    resposta = await client.patch(
        f"/funcionarios/{cozinha.id}",
        headers=auth_header(admin),
        json={"ativo": False},
    )

    assert resposta.status_code == 200
    assert resposta.json()["ativo"] is False
