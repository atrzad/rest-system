from httpx import AsyncClient

from app.models.funcionario import Funcionario
from app.models.mesa import Mesa
from app.models.produto import Produto
from tests.conftest import abrir_comanda, auth_header, criar_mesa, criar_produto


async def _abrir_comanda(client: AsyncClient, mesa: Mesa) -> str:
    return await abrir_comanda(client, mesa.numero)


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


async def _criar_pedido(client: AsyncClient, funcionario: Funcionario, comanda_id: str, produto: Produto) -> str:
    resposta = await client.post(
        "/pedidos",
        headers=auth_header(funcionario),
        json={"comanda_id": comanda_id, "itens": [{"produto_id": str(produto.id), "quantidade": 1}]},
    )
    return resposta.json()["id"]


async def _mudar_status(client: AsyncClient, funcionario: Funcionario, pedido_id: str, status: str) -> int:
    resposta = await client.patch(
        f"/pedidos/{pedido_id}/status", headers=auth_header(funcionario), json={"status": status}
    )
    return resposta.status_code


async def test_fluxo_completo_de_status(
    client: AsyncClient, cozinha: Funcionario, salao: Funcionario, mesa: Mesa, produto: Produto
):
    comanda_id = await _abrir_comanda(client, mesa)
    pedido_id = await _criar_pedido(client, salao, comanda_id, produto)

    assert await _mudar_status(client, cozinha, pedido_id, "em_preparo") == 200
    assert await _mudar_status(client, cozinha, pedido_id, "pronto") == 200
    assert await _mudar_status(client, salao, pedido_id, "entregue") == 200


async def test_cozinha_nao_pode_marcar_entregue(
    client: AsyncClient, cozinha: Funcionario, salao: Funcionario, mesa: Mesa, produto: Produto
):
    comanda_id = await _abrir_comanda(client, mesa)
    pedido_id = await _criar_pedido(client, salao, comanda_id, produto)
    await _mudar_status(client, cozinha, pedido_id, "em_preparo")
    await _mudar_status(client, cozinha, pedido_id, "pronto")

    assert await _mudar_status(client, cozinha, pedido_id, "entregue") == 403


async def test_salao_nao_pode_iniciar_preparo(
    client: AsyncClient, salao: Funcionario, mesa: Mesa, produto: Produto
):
    comanda_id = await _abrir_comanda(client, mesa)
    pedido_id = await _criar_pedido(client, salao, comanda_id, produto)

    assert await _mudar_status(client, salao, pedido_id, "em_preparo") == 403


async def test_salao_cancela_so_pedido_recebido(
    client: AsyncClient, salao: Funcionario, cozinha: Funcionario, mesa: Mesa, produto: Produto
):
    comanda_id = await _abrir_comanda(client, mesa)
    recebido = await _criar_pedido(client, salao, comanda_id, produto)
    em_preparo = await _criar_pedido(client, salao, comanda_id, produto)
    await _mudar_status(client, cozinha, em_preparo, "em_preparo")

    assert await _mudar_status(client, salao, recebido, "cancelado") == 200
    assert await _mudar_status(client, salao, em_preparo, "cancelado") == 403
    assert await _mudar_status(client, cozinha, em_preparo, "cancelado") == 200


async def test_admin_pode_fazer_qualquer_transicao_valida(
    client: AsyncClient, admin: Funcionario, mesa: Mesa, produto: Produto
):
    comanda_id = await _abrir_comanda(client, mesa)
    pedido_id = await _criar_pedido(client, admin, comanda_id, produto)

    for status in ("em_preparo", "pronto", "entregue"):
        assert await _mudar_status(client, admin, pedido_id, status) == 200


async def test_listar_pedidos_traz_itens_e_mesa_de_cada_pedido(
    client: AsyncClient, salao: Funcionario, mesa: Mesa, produto: Produto
):
    outra_mesa = await criar_mesa(2)
    outro_produto = await criar_produto(nome="Suco", preco="7.50")
    comanda_1 = await _abrir_comanda(client, mesa)
    comanda_2 = await _abrir_comanda(client, outra_mesa)
    await client.post(
        "/pedidos",
        headers=auth_header(salao),
        json={
            "comanda_id": comanda_1,
            "itens": [
                {"produto_id": str(produto.id), "quantidade": 2},
                {"produto_id": str(outro_produto.id), "quantidade": 1, "observacao": "sem gelo"},
            ],
        },
    )
    await _criar_pedido(client, salao, comanda_2, outro_produto)

    resposta = await client.get("/pedidos", headers=auth_header(salao))

    assert resposta.status_code == 200
    pedidos = resposta.json()
    assert [p["mesa_numero"] for p in pedidos] == [1, 2]
    itens_mesa_1 = sorted((i["produto_nome"], i["quantidade"], i["observacao"]) for i in pedidos[0]["itens"])
    assert itens_mesa_1 == [(produto.nome, 2, None), ("Suco", 1, "sem gelo")]
    assert [i["produto_nome"] for i in pedidos[1]["itens"]] == ["Suco"]
