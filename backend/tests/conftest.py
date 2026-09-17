import os
import uuid
from collections.abc import AsyncIterator

import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.auth.security import criar_access_token, hash_senha
from app.db.base import Base
from app.db.session import get_db
from app.main import app
from app.models.funcionario import Funcionario
from app.models.mesa import Mesa
from app.models.produto import Produto
from app.models.roles import Role

TEST_DATABASE_URL = os.environ.get(
    "TEST_DATABASE_URL",
    "postgresql+asyncpg://rest_system:rest_system@localhost:5432/rest_system_test",
)

engine = create_async_engine(TEST_DATABASE_URL)
TestSessionLocal = async_sessionmaker(engine, expire_on_commit=False)


@pytest_asyncio.fixture(scope="session", autouse=True)
async def _preparar_banco():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    yield
    await engine.dispose()


@pytest_asyncio.fixture(autouse=True)
async def _limpar_banco_apos_teste():
    yield
    async with engine.begin() as conn:
        for tabela in reversed(Base.metadata.sorted_tables):
            await conn.execute(tabela.delete())


@pytest_asyncio.fixture
async def client() -> AsyncIterator[AsyncClient]:
    async def override_get_db() -> AsyncIterator[AsyncSession]:
        async with TestSessionLocal() as session:
            yield session

    app.dependency_overrides[get_db] = override_get_db
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
    app.dependency_overrides.clear()


SENHA_PADRAO = "Senha123!"


async def criar_funcionario(role: Role, email: str | None = None) -> Funcionario:
    async with TestSessionLocal() as session:
        funcionario = Funcionario(
            nome=f"Teste {role.value}",
            email=email or f"{role.value}-{uuid.uuid4().hex[:8]}@teste.com",
            senha_hash=hash_senha(SENHA_PADRAO),
            role=role,
        )
        session.add(funcionario)
        await session.commit()
        await session.refresh(funcionario)
        return funcionario


@pytest_asyncio.fixture
async def admin() -> Funcionario:
    return await criar_funcionario(Role.admin)


@pytest_asyncio.fixture
async def salao() -> Funcionario:
    return await criar_funcionario(Role.salao)


@pytest_asyncio.fixture
async def cozinha() -> Funcionario:
    return await criar_funcionario(Role.cozinha)


async def criar_mesa(numero: int) -> Mesa:
    async with TestSessionLocal() as session:
        mesa = Mesa(numero=numero, capacidade=4)
        session.add(mesa)
        await session.commit()
        await session.refresh(mesa)
        return mesa


async def criar_produto(nome: str = "Produto Teste", preco: str = "10.00", disponivel: bool = True) -> Produto:
    async with TestSessionLocal() as session:
        produto = Produto(nome=nome, categoria="Geral", preco=preco, disponivel=disponivel)
        session.add(produto)
        await session.commit()
        await session.refresh(produto)
        return produto


@pytest_asyncio.fixture
async def mesa() -> Mesa:
    return await criar_mesa(1)


@pytest_asyncio.fixture
async def produto() -> Produto:
    return await criar_produto()


def auth_header(funcionario: Funcionario) -> dict[str, str]:
    token = criar_access_token(
        sub=str(funcionario.id),
        role=funcionario.role.value,
        nome=funcionario.nome,
        email=funcionario.email,
    )
    return {"Authorization": f"Bearer {token}"}
