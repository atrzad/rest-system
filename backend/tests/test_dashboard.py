from datetime import date, datetime, timedelta, timezone
from decimal import Decimal

from httpx import AsyncClient

from app.models.funcionario import Funcionario
from app.models.mesa import Mesa
from app.models.venda_evento import VendaEvento
from app.services import dashboard_service
from tests.conftest import TestSessionLocal, abrir_comanda, auth_header, criar_mesa, criar_produto


async def _lancar(client: AsyncClient, funcionario: Funcionario, comanda_id: str, itens) -> str:
    resposta = await client.post(
        "/pedidos",
        headers=auth_header(funcionario),
        json={"comanda_id": comanda_id, "itens": [{"produto_id": str(p.id), "quantidade": q} for p, q in itens]},
    )
    assert resposta.status_code == 201, resposta.text
    return resposta.json()["id"]


async def _status(client: AsyncClient, admin: Funcionario, pedido_id: str, *passos: str) -> None:
    for passo in passos:
        resposta = await client.patch(f"/pedidos/{pedido_id}/status", headers=auth_header(admin), json={"status": passo})
        assert resposta.status_code == 200, resposta.text


async def test_dashboard_consolida_vendas_do_dia(client: AsyncClient, admin: Funcionario, mesa: Mesa):
    outra_mesa = await criar_mesa(2)
    prato = await criar_produto(nome="Prato", preco="40.00")
    suco = await criar_produto(nome="Suco", preco="10.00")

    # Mesa 1: 2 pratos + 1 suco, com taxa → 90,00 + 9,00
    comanda_1 = await abrir_comanda(client, mesa.numero)
    pedido_1 = await _lancar(client, admin, comanda_1, [(prato, 2), (suco, 1)])
    await _status(client, admin, pedido_1, "em_preparo", "pronto", "entregue")
    await client.post(f"/comandas/{comanda_1}/fechar", headers=auth_header(admin), json={"taxa_servico": True})

    # Mesa 2: 3 sucos (sem taxa) + 1 prato cancelado → 30,00
    comanda_2 = await abrir_comanda(client, outra_mesa.numero)
    pedido_2 = await _lancar(client, admin, comanda_2, [(suco, 3)])
    cancelado = await _lancar(client, admin, comanda_2, [(prato, 1)])
    await _status(client, admin, cancelado, "cancelado")
    await _status(client, admin, pedido_2, "em_preparo", "pronto", "entregue")
    await client.post(f"/comandas/{comanda_2}/fechar", headers=auth_header(admin), json={"taxa_servico": False})

    resposta = await client.get("/dashboard/vendas", headers=auth_header(admin))

    assert resposta.status_code == 200, resposta.text
    d = resposta.json()
    assert d["faturamento"] == "129.00"
    assert d["taxa_servico"] == "9.00"
    assert d["comandas_fechadas"] == 2
    assert d["ticket_medio"] == "64.50"
    assert d["comandas_abertas_agora"] == 0
    assert d["consumo"] == "120.00"
    assert d["itens_vendidos"] == 6
    assert d["granularidade"] == "hora"
    assert len(d["serie"]) == 24
    assert sum(Decimal(p["valor"]) for p in d["serie"]) == Decimal("120.00")
    assert [(p["nome"], p["quantidade"], p["valor"]) for p in d["top_produtos"]] == [
        ("Prato", 2, "80.00"),
        ("Suco", 4, "40.00"),
    ]
    assert [(c["categoria"], c["valor"]) for c in d["por_categoria"]] == [("Geral", "120.00")]
    assert d["tempo_medio_preparo_min"] is not None


async def test_dashboard_so_admin(client: AsyncClient, salao: Funcionario):
    assert (await client.get("/dashboard/vendas")).status_code == 401
    assert (await client.get("/dashboard/vendas", headers=auth_header(salao))).status_code == 403


async def test_dashboard_periodo_invalido(client: AsyncClient, admin: Funcionario):
    resposta = await client.get(
        "/dashboard/vendas?inicio=2026-10-10&fim=2026-10-01", headers=auth_header(admin)
    )

    assert resposta.status_code == 400


async def _fato(ocorrido_em: datetime, valor: str, tipo: str = "pedido_item_criado") -> None:
    async with TestSessionLocal() as session:
        session.add(
            VendaEvento(
                tipo=tipo,
                valor=Decimal(valor),
                quantidade=1,
                ocorrido_em=ocorrido_em,
                payload={"categoria": "Bebidas", "taxa_servico": "0.00"},
            )
        )
        await session.commit()


async def test_fronteira_do_dia_usa_o_fuso_de_manaus(client: AsyncClient, admin: Funcionario):
    # 13/10 às 23:30 em Manaus (UTC-4) = 14/10 às 03:30 UTC: tem que contar no dia 13.
    await _fato(datetime(2026, 10, 14, 3, 30, tzinfo=timezone.utc), "50.00")
    # 14/10 às 00:10 em Manaus: conta no dia 14.
    await _fato(datetime(2026, 10, 14, 4, 10, tzinfo=timezone.utc), "7.00")

    dia_13 = (await client.get("/dashboard/vendas?inicio=2026-10-13&fim=2026-10-13", headers=auth_header(admin))).json()
    dia_14 = (await client.get("/dashboard/vendas?inicio=2026-10-14&fim=2026-10-14", headers=auth_header(admin))).json()

    assert dia_13["consumo"] == "50.00"
    assert next(p for p in dia_13["serie"] if p["rotulo"] == "23h")["valor"] == "50.00"
    assert dia_14["consumo"] == "7.00"
    assert next(p for p in dia_14["serie"] if p["rotulo"] == "0h")["valor"] == "7.00"


async def test_periodo_de_varios_dias_agrupa_por_dia(client: AsyncClient, admin: Funcionario):
    await _fato(datetime(2026, 10, 11, 18, 0, tzinfo=timezone.utc), "10.00")
    await _fato(datetime(2026, 10, 13, 18, 0, tzinfo=timezone.utc), "20.00")
    await _fato(datetime(2026, 10, 13, 19, 0, tzinfo=timezone.utc), "30.00", tipo="comanda_fechada")

    d = (await client.get("/dashboard/vendas?inicio=2026-10-07&fim=2026-10-13", headers=auth_header(admin))).json()

    assert d["granularidade"] == "dia"
    assert [p["rotulo"] for p in d["serie"]] == ["07/10", "08/10", "09/10", "10/10", "11/10", "12/10", "13/10"]
    assert [p["valor"] for p in d["serie"]][-3:] == ["10.00", "0.00", "20.00"]
    assert d["faturamento"] == "30.00"
    assert d["comandas_fechadas"] == 1


def test_hoje_local_usa_o_fuso_configurado(monkeypatch):
    monkeypatch.setattr(dashboard_service.settings, "timezone_local", "Pacific/Kiritimati")  # UTC+14
    hoje_utc = datetime.now(timezone.utc).date()

    assert dashboard_service.hoje_local() in (hoje_utc, hoje_utc + timedelta(days=1))
    assert isinstance(dashboard_service.hoje_local(), date)


async def test_atalho_dias_conta_ate_hoje(client: AsyncClient, admin: Funcionario):
    d = (await client.get("/dashboard/vendas?dias=7", headers=auth_header(admin))).json()

    hoje = dashboard_service.hoje_local()
    assert d["fim"] == hoje.isoformat()
    assert d["inicio"] == (hoje - timedelta(days=6)).isoformat()
    assert len(d["serie"]) == 7
