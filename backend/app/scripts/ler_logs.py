"""Lê os logs internos direto do banco. Uso pensado para quem tem acesso
root/SSH ao servidor — não existe nenhum endpoint HTTP equivalente.

    .venv/bin/python -m app.scripts.ler_logs
    .venv/bin/python -m app.scripts.ler_logs --nivel ERROR --limite 100
"""

import argparse
import asyncio
import gzip

from sqlalchemy import select

from app.db.session import SessionLocal
from app.models.log_entry import LogEntry


def _desempacotar(dados: bytes | None, comprimido: bool) -> str | None:
    if dados is None:
        return None
    bruto = gzip.decompress(dados) if comprimido else dados
    return bruto.decode("utf-8")


async def listar(nivel: str | None, limite: int) -> None:
    async with SessionLocal() as db:
        query = select(LogEntry).order_by(LogEntry.id.desc()).limit(limite)
        if nivel:
            query = query.where(LogEntry.nivel == nivel.upper())

        resultado = await db.execute(query)
        entradas = list(reversed(resultado.scalars().all()))

        if not entradas:
            print("Nenhum log encontrado.")
            return

        for entrada in entradas:
            mensagem = _desempacotar(entrada.mensagem, entrada.mensagem_comprimida)
            print(f"[{entrada.criado_em.isoformat()}] {entrada.nivel:8s} {entrada.logger_nome}: {mensagem}")
            contexto = _desempacotar(entrada.contexto, entrada.contexto_comprimida)
            if contexto:
                print(contexto.rstrip())


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--nivel", default=None, help="DEBUG, INFO, WARNING, ERROR ou CRITICAL")
    parser.add_argument("--limite", type=int, default=50)
    args = parser.parse_args()

    asyncio.run(listar(args.nivel, args.limite))
