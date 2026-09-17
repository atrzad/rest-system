from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.routers import auth, comandas, funcionarios, mesas, produtos

app = FastAPI(title="Rest System API")
app.include_router(auth.router)
app.include_router(funcionarios.router)
app.include_router(produtos.router)
app.include_router(mesas.router)
app.include_router(comandas.router)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}
