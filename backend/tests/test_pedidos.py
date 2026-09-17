from httpx import AsyncClient

from app.models.funcionario import Funcionario
from app.models.mesa import Mesa
from app.models.produto import Produto
from tests.conftest import auth_header, criar_produto


async def _abrir_comanda(client: AsyncClient, mesa: Mesa) -> str:
    resposta = await client.post("/comandas/abrir-por-mesa", json={"numero_mesa": mesa.numero, "origem": "garcom"})
    return resposta.json()["id"]


async def test_criar_pedido_com_sucesso(client: AsyncClient, salao: Funcionario, mesa: Mesa, produto: Produto):
    comanda_id = await _abrir_comanda(client, mesa)

    resposta = await client.post(
        "/pedidos",
        headers=auth_header(salao),
        json={"comanda_id": comanda_id, "itens": [{"produto_id": str(produto.id), "quantidade": 2}]},
    )

    assert resposta.status_code == 201
    corpo = resposta.json()
    assert corpo["status"] == "recebido"
    assert corpo["itens"][0]["quantidade"] == 2
    assert corpo["itens"][0]["produto_nome"] == produto.nome


async def test_criar_pedido_em_comanda_inexistente_retorna_404(
    client: AsyncClient, salao: Funcionario, produto: Produto
):
    resposta = await client.post(
        "/pedidos",
        headers=auth_header(salao),
        json={
            "comanda_id": "00000000-0000-0000-0000-000000000000",
            "itens": [{"produto_id": str(produto.id), "quantidade": 1}],
        },
    )

    assert resposta.status_code == 404


async def test_criar_pedido_com_produto_indisponivel_retorna_400(
    client: AsyncClient, salao: Funcionario, mesa: Mesa
):
    produto_indisponivel = await criar_produto(nome="Fora do cardápio", disponivel=False)
    comanda_id = await _abrir_comanda(client, mesa)

    resposta = await client.post(
        "/pedidos",
        headers=auth_header(salao),
        json={"comanda_id": comanda_id, "itens": [{"produto_id": str(produto_indisponivel.id), "quantidade": 1}]},
    )

    assert resposta.status_code == 400


async def test_criar_pedido_em_comanda_fechada_retorna_400(
    client: AsyncClient, salao: Funcionario, mesa: Mesa, produto: Produto
):
    comanda_id = await _abrir_comanda(client, mesa)
    await client.post(f"/comandas/{comanda_id}/fechar", headers=auth_header(salao))

    resposta = await client.post(
        "/pedidos",
        headers=auth_header(salao),
        json={"comanda_id": comanda_id, "itens": [{"produto_id": str(produto.id), "quantidade": 1}]},
    )

    assert resposta.status_code == 400


async def test_transicao_de_status_invalida_retorna_400(
    client: AsyncClient, salao: Funcionario, mesa: Mesa, produto: Produto
):
    comanda_id = await _abrir_comanda(client, mesa)
    pedido = await client.post(
        "/pedidos",
        headers=auth_header(salao),
        json={"comanda_id": comanda_id, "itens": [{"produto_id": str(produto.id), "quantidade": 1}]},
    )
    pedido_id = pedido.json()["id"]

    resposta = await client.patch(
        f"/pedidos/{pedido_id}/status", headers=auth_header(salao), json={"status": "entregue"}
    )

    assert resposta.status_code == 400


async def test_fluxo_completo_de_status(client: AsyncClient, cozinha: Funcionario, mesa: Mesa, produto: Produto):
    comanda_id = await _abrir_comanda(client, mesa)
    pedido = await client.post(
        "/pedidos",
        headers=auth_header(cozinha),
        json={"comanda_id": comanda_id, "itens": [{"produto_id": str(produto.id), "quantidade": 1}]},
    )
    pedido_id = pedido.json()["id"]

    for status in ("em_preparo", "pronto", "entregue"):
        resposta = await client.patch(
            f"/pedidos/{pedido_id}/status", headers=auth_header(cozinha), json={"status": status}
        )
        assert resposta.status_code == 200
        assert resposta.json()["status"] == status
