"""Handler de logging que persiste no Postgres (tabela log_entry), sem nenhum
endpoint HTTP — a leitura é só via terminal com acesso root/SSH ao banco
(ver app/scripts/ler_logs.py). Mensagens/contextos grandes são comprimidos
com gzip antes de gravar, pra não pesar o banco.
"""

import asyncio
import gzip
import logging
import traceback
from datetime import datetime, timezone
from typing import TypedDict

from app.db.session import SessionLocal
from app.models.log_entry import LogEntry

LIMIAR_COMPRESSAO_BYTES = 200


class _ItemLog(TypedDict):
    nivel: str
    logger_nome: str
    mensagem: str
    contexto: str | None
    criado_em: datetime


_fila: asyncio.Queue[_ItemLog] | None = None


def _fila_de_logs() -> asyncio.Queue[_ItemLog]:
    global _fila
    if _fila is None:
        _fila = asyncio.Queue()
    return _fila


class DatabaseLogHandler(logging.Handler):
    """Handler síncrono (chamado direto pelo `logging`) que só enfileira —
    quem grava no banco é a task `escrever_logs`, rodando no mesmo event loop."""

    def emit(self, record: logging.LogRecord) -> None:
        try:
            contexto = None
            if record.exc_info:
                contexto = "".join(traceback.format_exception(*record.exc_info))

            _fila_de_logs().put_nowait(
                {
                    "nivel": record.levelname,
                    "logger_nome": record.name,
                    "mensagem": self.format(record),
                    "contexto": contexto,
                    "criado_em": datetime.now(timezone.utc),
                }
            )
        except Exception:
            self.handleError(record)


def _empacotar(texto: str | None) -> tuple[bytes | None, bool]:
    if texto is None:
        return None, False
    dados = texto.encode("utf-8")
    if len(dados) < LIMIAR_COMPRESSAO_BYTES:
        return dados, False
    return gzip.compress(dados), True


async def escrever_logs() -> None:
    """Task de background: drena a fila e grava em lote no Postgres."""
    fila = _fila_de_logs()

    while True:
        lote = [await fila.get()]
        try:
            while len(lote) < 50:
                lote.append(fila.get_nowait())
        except asyncio.QueueEmpty:
            pass

        try:
            async with SessionLocal() as db:
                for item in lote:
                    mensagem_bytes, msg_comprimida = _empacotar(item["mensagem"])
                    contexto_bytes, ctx_comprimida = _empacotar(item["contexto"])
                    db.add(
                        LogEntry(
                            nivel=item["nivel"],
                            logger_nome=item["logger_nome"],
                            mensagem=mensagem_bytes,
                            mensagem_comprimida=msg_comprimida,
                            contexto=contexto_bytes,
                            contexto_comprimida=ctx_comprimida,
                            criado_em=item["criado_em"],
                        )
                    )
                await db.commit()
        except Exception:
            # Nunca deixa um erro ao gravar log derrubar a aplicação; manda pro stderr como fallback.
            traceback.print_exc()


def configurar_logging() -> None:
    handler = DatabaseLogHandler()
    handler.setFormatter(logging.Formatter("%(message)s"))
    logging.getLogger().addHandler(handler)
    logging.getLogger().setLevel(logging.INFO)
