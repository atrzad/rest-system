"""Agregações do dashboard de vendas, em SQL, a partir da tabela venda_evento."""

from datetime import date, datetime, time, timedelta
from decimal import Decimal
from zoneinfo import ZoneInfo

from sqlalchemy import Numeric, func, literal, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.models.comanda import Comanda, ComandaStatus
from app.models.produto import Produto
from app.models.venda_evento import VendaEvento
from app.schemas.dashboard import CategoriaVenda, DashboardVendas, PontoSerie, ProdutoRanking

TIPOS_ITEM = ("pedido_item_criado", "pedido_item_cancelado")
ZERO = Decimal("0.00")


def hoje_local() -> date:
    return datetime.now(ZoneInfo(settings.timezone_local)).date()


def _intervalo_utc(inicio: date, fim: date) -> tuple[datetime, datetime]:
    """[meia-noite local de `inicio`, meia-noite local do dia seguinte a `fim`)."""
    fuso = ZoneInfo(settings.timezone_local)
    return datetime.combine(inicio, time.min, fuso), datetime.combine(fim + timedelta(days=1), time.min, fuso)


async def vendas(db: AsyncSession, inicio: date, fim: date) -> DashboardVendas:
    de, ate = _intervalo_utc(inicio, fim)
    no_periodo = (VendaEvento.ocorrido_em >= de, VendaEvento.ocorrido_em < ate)
    e_item = VendaEvento.tipo.in_(TIPOS_ITEM)

    # --- Faturamento: comandas fechadas no período ---
    faturamento, taxa, fechadas = (
        await db.execute(
            select(
                func.coalesce(func.sum(VendaEvento.valor), 0),
                func.coalesce(func.sum(VendaEvento.payload["taxa_servico"].astext.cast(Numeric(10, 2))), 0),
                func.count(),
            ).where(VendaEvento.tipo == "comanda_fechada", *no_periodo)
        )
    ).one()
    faturamento = Decimal(faturamento).quantize(Decimal("0.01"))
    ticket_medio = (faturamento / fechadas).quantize(Decimal("0.01")) if fechadas else ZERO

    abertas_agora = (
        await db.execute(select(func.count()).select_from(Comanda).where(Comanda.status == ComandaStatus.aberta))
    ).scalar_one()

    # --- Consumo (itens lançados - cancelados) ---
    consumo, itens_vendidos = (
        await db.execute(
            select(
                func.coalesce(func.sum(VendaEvento.valor), 0), func.coalesce(func.sum(VendaEvento.quantidade), 0)
            ).where(e_item, *no_periodo)
        )
    ).one()

    # --- Série por hora (1 dia) ou por dia (vários dias), no horário local ---
    granularidade = "hora" if inicio == fim else "dia"
    local = func.timezone(settings.timezone_local, VendaEvento.ocorrido_em)
    balde = func.date_trunc("hour" if granularidade == "hora" else "day", local).label("balde")
    linhas = (
        await db.execute(
            select(balde, func.sum(VendaEvento.valor), func.sum(VendaEvento.quantidade))
            .where(e_item, *no_periodo)
            .group_by(balde)
        )
    ).all()
    por_balde = {b: (Decimal(v), int(q)) for b, v, q in linhas}
    serie = []
    if granularidade == "hora":
        for hora in range(24):
            ponto = datetime.combine(inicio, time(hour=hora))
            valor, qtd = por_balde.get(ponto, (ZERO, 0))
            serie.append(PontoSerie(rotulo=f"{hora}h", inicio=ponto.isoformat(), valor=valor, itens=qtd))
    else:
        dia = inicio
        while dia <= fim:
            ponto = datetime.combine(dia, time.min)
            valor, qtd = por_balde.get(ponto, (ZERO, 0))
            serie.append(PontoSerie(rotulo=dia.strftime("%d/%m"), inicio=ponto.isoformat(), valor=valor, itens=qtd))
            dia += timedelta(days=1)

    # --- Top 10 produtos por valor vendido (nome atual do cadastro) ---
    valor_produto = func.sum(VendaEvento.valor).label("valor")
    ranking = (
        await db.execute(
            select(VendaEvento.produto_id, Produto.nome, func.sum(VendaEvento.quantidade), valor_produto)
            .join(Produto, VendaEvento.produto_id == Produto.id)
            .where(e_item, *no_periodo)
            .group_by(VendaEvento.produto_id, Produto.nome)
            .having(func.sum(VendaEvento.quantidade) > 0)
            .order_by(valor_produto.desc(), Produto.nome)
            .limit(10)
        )
    ).all()

    # --- Por categoria (categoria gravada no momento da venda) ---
    categoria = func.coalesce(VendaEvento.payload["categoria"].astext, literal("Sem categoria")).label("categoria")
    valor_categoria = func.sum(VendaEvento.valor).label("valor")
    categorias = (
        await db.execute(
            select(categoria, func.sum(VendaEvento.quantidade), valor_categoria)
            .where(e_item, *no_periodo)
            .group_by(categoria)
            .having(func.sum(VendaEvento.quantidade) > 0)
            .order_by(valor_categoria.desc())
        )
    ).all()

    # --- Tempo médio de preparo: do "em_preparo" ao "pronto" de cada pedido ---
    para = VendaEvento.payload["para"].astext
    por_pedido = (
        select(
            VendaEvento.pedido_id,
            func.min(VendaEvento.ocorrido_em).filter(para == "em_preparo").label("inicio"),
            func.min(VendaEvento.ocorrido_em).filter(para == "pronto").label("pronto"),
        )
        .where(VendaEvento.tipo == "pedido_status", *no_periodo)
        .group_by(VendaEvento.pedido_id)
        .subquery()
    )
    segundos = func.extract("epoch", por_pedido.c.pronto - por_pedido.c.inicio)
    tempo_medio = (
        await db.execute(
            select(func.avg(segundos)).where(por_pedido.c.inicio.is_not(None), por_pedido.c.pronto.is_not(None))
        )
    ).scalar_one()

    return DashboardVendas(
        inicio=inicio,
        fim=fim,
        fuso=settings.timezone_local,
        faturamento=faturamento,
        taxa_servico=Decimal(taxa).quantize(Decimal("0.01")),
        comandas_fechadas=fechadas,
        ticket_medio=ticket_medio,
        comandas_abertas_agora=abertas_agora,
        consumo=Decimal(consumo).quantize(Decimal("0.01")),
        itens_vendidos=int(itens_vendidos),
        tempo_medio_preparo_min=round(float(tempo_medio) / 60, 1) if tempo_medio is not None else None,
        granularidade=granularidade,
        serie=serie,
        top_produtos=[
            ProdutoRanking(produto_id=str(pid), nome=nome, quantidade=int(q), valor=Decimal(v))
            for pid, nome, q, v in ranking
        ],
        por_categoria=[CategoriaVenda(categoria=c, quantidade=int(q), valor=Decimal(v)) for c, q, v in categorias],
    )
