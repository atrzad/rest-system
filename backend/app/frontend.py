"""Serve o build do frontend (frontend/dist) pela própria API, na mesma origem.

Usado em produção (atrás do HTTPS do Tailscale): um processo só, sem CORS e com o WebSocket
no mesmo endereço. Em desenvolvimento o Vite serve o frontend e isto fica desligado.
"""

from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles


def servir_frontend(app: FastAPI, pasta: str) -> None:
    if not pasta:
        return
    dist = Path(pasta).resolve()
    index = dist / "index.html"
    if not index.is_file():
        raise RuntimeError(f"FRONTEND_DIST={pasta} não tem index.html (rodou o npm run build?)")

    # Arquivos com hash no nome: podem ficar em cache "para sempre" no navegador.
    app.mount("/assets", StaticFiles(directory=dist / "assets"), name="frontend-assets")

    @app.get("/{caminho:path}", include_in_schema=False)
    async def spa(caminho: str) -> FileResponse:
        arquivo = (dist / caminho).resolve()
        # Arquivos soltos da raiz do build (favicon etc.), sem sair da pasta.
        if caminho and arquivo.is_file() and arquivo.is_relative_to(dist):
            return FileResponse(arquivo)
        if "." in caminho.rsplit("/", 1)[-1]:
            raise HTTPException(404)  # arquivo que não existe: 404 de verdade, não a página
        # Qualquer outra rota é do React Router (/salao/mesas, /mesa/4...): devolve o index.html
        # sem cache, para um deploy novo chegar na próxima visita.
        return FileResponse(index, headers={"Cache-Control": "no-cache"})
