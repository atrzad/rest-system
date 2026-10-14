import asyncio

from httpx import AsyncClient

from app.models.funcionario import Funcionario
from app.models.mesa import Mesa
from tests.conftest import auth_header, criar_produto


async def _abrir_comanda(client: AsyncClient, mesa: Mesa) -> str:
    resposta = await client.post("/comandas/abrir-por-mesa", json={"numero_mesa": mesa.numero, "origem": "garcom"})
    return resposta.json()["id"]


async def _lancar(client: AsyncClient, salao: Funcionario, comanda_id: str, itens: list[tuple[str, int]]) -> str:
    resposta = await client.post(
        "/pedidos",
        headers=auth_header(salao),
        json={"comanda_id": comanda_id, "itens": [{"produto_id": p, "quantidade": q} for p, q in itens]},
    )
    assert resposta.status_code == 201
    return resposta.json()["id"]


async def _entregar(client: AsyncClient, admin: Funcionario, pedido_id: str) -> None:
    for status in ("em_preparo", "pronto", "entregue"):
        resposta = await client.patch(
            f"/pedidos/{pedido_id}/status", headers=auth_header(admin), json={"status": status}
        )
        assert resposta.status_code == 200


async def test_conta_soma_itens_e_ignora_cancelados(
    client: AsyncClient, salao: Funcionario, mesa: Mesa
):
    prato = await criar_produto(nome="Prato", preco="32.90")
    refri = await criar_produto(nome="Refri", preco="6.00")
    comanda_id = await _abrir_comanda(client, mesa)
    await _lancar(client, salao, comanda_id, [(str(prato.id), 2), (str(refri.id), 1)])
    cancelado = await _lancar(client, salao, comanda_id, [(str(prato.id), 5)])
    await client.patch(f"/pedidos/{cancelado}/status", headers=auth_header(salao), json={"status": "cancelado"})

    com_taxa = (await client.get(f"/comandas/{comanda_id}/conta", headers=auth_header(salao))).json()
    sem_taxa = (await client.get(f"/comandas/{comanda_id}/conta?taxa=false", headers=auth_header(salao))).json()

    assert com_taxa["subtotal"] == "71.80"
    assert com_taxa["taxa_servico"] == "7.18"
    assert com_taxa["total"] == "78.98"
    assert {(i["produto_nome"], i["quantidade"], i["valor"]) for i in com_taxa["itens"]} == {
        ("Prato", 2, "65.80"),
        ("Refri", 1, "6.00"),
    }
    assert com_taxa["pedidos_pendentes"] == 1
    assert sem_taxa["taxa_servico"] == "0.00"
    assert sem_taxa["total"] == "71.80"


async def test_fechar_com_pedido_pendente_retorna_409(
    client: AsyncClient, salao: Funcionario, mesa: Mesa
):
    prato = await criar_produto(nome="Prato", preco="20.00")
    comanda_id = await _abrir_comanda(client, mesa)
    await _lancar(client, salao, comanda_id, [(str(prato.id), 1)])

    resposta = await client.post(f"/comandas/{comanda_id}/fechar", headers=auth_header(salao))

    assert resposta.status_code == 409
    assert "pendente" in resposta.json()["detail"]


async def test_fechar_grava_total_com_e_sem_taxa(
    client: AsyncClient, salao: Funcionario, admin: Funcionario, mesa: Mesa
):
    prato = await criar_produto(nome="Prato", preco="45.00")
    comanda_id = await _abrir_comanda(client, mesa)
    pedido_id = await _lancar(client, salao, comanda_id, [(str(prato.id), 2)])
    await _entregar(client, admin, pedido_id)

    resposta = await client.post(
        f"/comandas/{comanda_id}/fechar", headers=auth_header(salao), json={"taxa_servico": False}
    )

    assert resposta.status_code == 200
    corpo = resposta.json()
    assert corpo["status"] == "fechada"
    assert (corpo["subtotal"], corpo["taxa_servico"], corpo["total"]) == ("90.00", "0.00", "90.00")


async def test_fechar_sem_corpo_aplica_taxa_por_padrao(
    client: AsyncClient, salao: Funcionario, admin: Funcionario, mesa: Mesa
):
    prato = await criar_produto(nome="Prato", preco="45.00")
    comanda_id = await _abrir_comanda(client, mesa)
    pedido_id = await _lancar(client, salao, comanda_id, [(str(prato.id), 2)])
    await _entregar(client, admin, pedido_id)

    corpo = (await client.post(f"/comandas/{comanda_id}/fechar", headers=auth_header(salao))).json()

    assert corpo["total"] == "99.00"


async def test_abertura_simultanea_cria_uma_comanda_so(client: AsyncClient, salao: Funcionario, mesa: Mesa):
    respostas = await asyncio.gather(
        *(
            client.post("/comandas/abrir-por-mesa", json={"numero_mesa": mesa.numero, "origem": "garcom"})
            for _ in range(5)
        )
    )

    assert all(r.status_code == 200 for r in respostas)
    assert len({r.json()["id"] for r in respostas}) == 1
    abertas = (await client.get("/comandas?status_filtro=aberta", headers=auth_header(salao))).json()
    assert len(abertas) == 1


async def test_abertura_concorrente_cai_no_indice_e_devolve_a_existente(
    client: AsyncClient, mesa: Mesa, monkeypatch
):
    from app.services import comanda_service

    primeira = await _abrir_comanda(client, mesa)

    # Simula a corrida: a checagem prévia "não vê" a comanda já aberta, então o INSERT bate no índice único.
    original = comanda_service._comanda_aberta_da_mesa
    chamadas = {"n": 0}

    async def nao_ve_na_primeira(db, mesa_id):
        chamadas["n"] += 1
        return None if chamadas["n"] == 1 else await original(db, mesa_id)

    monkeypatch.setattr(comanda_service, "_comanda_aberta_da_mesa", nao_ve_na_primeira)
    resposta = await client.post("/comandas/abrir-por-mesa", json={"numero_mesa": mesa.numero, "origem": "garcom"})

    assert resposta.status_code == 200
    assert resposta.json()["id"] == primeira
    assert chamadas["n"] == 2
