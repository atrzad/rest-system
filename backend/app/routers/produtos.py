import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.deps import get_current_user, require_role
from app.db.session import get_db
from app.models.produto import Produto
from app.models.roles import Role
from app.schemas.produto import ProdutoCreate, ProdutoOut, ProdutoUpdate

router = APIRouter(prefix="/produtos", tags=["produtos"])


@router.get("", response_model=list[ProdutoOut], dependencies=[Depends(get_current_user)])
async def listar(db: AsyncSession = Depends(get_db)) -> list[Produto]:
    resultado = await db.execute(select(Produto).order_by(Produto.categoria, Produto.nome))
    return list(resultado.scalars().all())


@router.post(
    "",
    response_model=ProdutoOut,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_role(Role.admin))],
)
async def criar(dados: ProdutoCreate, db: AsyncSession = Depends(get_db)) -> Produto:
    produto = Produto(**dados.model_dump())
    db.add(produto)
    await db.commit()
    await db.refresh(produto)
    return produto


@router.patch("/{produto_id}", response_model=ProdutoOut, dependencies=[Depends(require_role(Role.admin))])
async def atualizar(produto_id: uuid.UUID, dados: ProdutoUpdate, db: AsyncSession = Depends(get_db)) -> Produto:
    produto = await db.get(Produto, produto_id)
    if produto is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Produto não encontrado")

    for campo, valor in dados.model_dump(exclude_unset=True).items():
        setattr(produto, campo, valor)

    await db.commit()
    await db.refresh(produto)
    return produto
