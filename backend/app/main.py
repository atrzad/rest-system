import asyncio
import contextlib
import logging
from collections.abc import AsyncIterator

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.config import settings
from app.logging_db import configurar_logging, escrever_logs
from app.routers import auth, comandas, funcionarios, mesas, pedidos, produtos, ws
from app.ws.router_bridge import escutar_eventos

logger = logging.getLogger(__name__)


@contextlib.asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    configurar_logging()
    tasks = [
        asyncio.create_task(escutar_eventos()),
        asyncio.create_task(escrever_logs()),
    ]
    yield
    for task in tasks:
        task.cancel()
    for task in tasks:
        with contextlib.suppress(asyncio.CancelledError):
            await task


app = FastAPI(title="Rest System API", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(Exception)
async def tratar_excecao_nao_prevista(request: Request, exc: Exception) -> JSONResponse:
    logger.exception("Erro não tratado em %s %s", request.method, request.url.path)
    return JSONResponse(status_code=500, content={"detail": "Erro interno do servidor"})


app.include_router(auth.router)
app.include_router(funcionarios.router)
app.include_router(produtos.router)
app.include_router(mesas.router)
app.include_router(comandas.router)
app.include_router(pedidos.router)
app.include_router(ws.router)


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}
