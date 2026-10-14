from pathlib import Path

import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient

from app.frontend import servir_frontend


@pytest.fixture
def dist(tmp_path: Path) -> Path:
    (tmp_path / "assets").mkdir()
    (tmp_path / "index.html").write_text("<html>app</html>")
    (tmp_path / "assets" / "index-abc123.js").write_text("console.log(1)")
    (tmp_path / "favicon.svg").write_text("<svg/>")
    (tmp_path.parent / "segredo.txt").write_text("não pode vazar")
    return tmp_path


async def _cliente(dist: Path) -> AsyncClient:
    app = FastAPI()

    @app.get("/mesas")
    async def rota_da_api() -> dict:
        return {"api": True}

    servir_frontend(app, str(dist))
    return AsyncClient(transport=ASGITransport(app=app), base_url="http://test")


async def test_rotas_do_react_devolvem_o_index(dist: Path):
    async with await _cliente(dist) as c:
        for caminho in ("/", "/salao/mesas", "/mesa/4"):
            resposta = await c.get(caminho, params={"t": "ABC"})
            assert resposta.status_code == 200
            assert resposta.text == "<html>app</html>"
            assert resposta.headers["cache-control"] == "no-cache"


async def test_api_tem_prioridade_e_arquivos_sao_servidos(dist: Path):
    async with await _cliente(dist) as c:
        assert (await c.get("/mesas")).json() == {"api": True}
        assert (await c.get("/assets/index-abc123.js")).text == "console.log(1)"
        assert (await c.get("/favicon.svg")).text == "<svg/>"


async def test_arquivo_inexistente_e_fuga_de_pasta_dao_404(dist: Path):
    async with await _cliente(dist) as c:
        assert (await c.get("/nao-existe.png")).status_code == 404
        assert (await c.get("/..%2Fsegredo.txt")).status_code == 404


def test_pasta_sem_build_falha_logo(tmp_path: Path):
    with pytest.raises(RuntimeError, match="index.html"):
        servir_frontend(FastAPI(), str(tmp_path))
