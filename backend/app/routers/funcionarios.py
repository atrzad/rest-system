import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.deps import require_role
from app.auth.security import hash_senha
from app.db.session import get_db
from app.models.funcionario import Funcionario
from app.models.roles import Role
from app.schemas.auth import CurrentUser
from app.schemas.funcionario import FuncionarioCreate, FuncionarioOut, FuncionarioUpdate

router = APIRouter(
    prefix="/funcionarios",
    tags=["funcionarios"],
    dependencies=[Depends(require_role(Role.admin))],
)


@router.get("", response_model=list[FuncionarioOut])
async def listar(db: AsyncSession = Depends(get_db)) -> list[Funcionario]:
    resultado = await db.execute(select(Funcionario).order_by(Funcionario.nome))
    return list(resultado.scalars().all())


@router.post("", response_model=FuncionarioOut, status_code=status.HTTP_201_CREATED)
async def criar(dados: FuncionarioCreate, db: AsyncSession = Depends(get_db)) -> Funcionario:
    existente = await db.execute(select(Funcionario).where(Funcionario.email == dados.email))
    if existente.scalar_one_or_none() is not None:
        raise HTTPException(status.HTTP_409_CONFLICT, "Já existe um funcionário com este e-mail")

    funcionario = Funcionario(
        nome=dados.nome,
        email=dados.email,
        senha_hash=hash_senha(dados.senha),
        role=dados.role,
    )
    db.add(funcionario)
    await db.commit()
    await db.refresh(funcionario)
    return funcionario


async def _buscar_ou_404(funcionario_id: uuid.UUID, db: AsyncSession) -> Funcionario:
    funcionario = await db.get(Funcionario, funcionario_id)
    if funcionario is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Funcionário não encontrado")
    return funcionario


@router.patch("/{funcionario_id}", response_model=FuncionarioOut)
async def atualizar(
    funcionario_id: uuid.UUID,
    dados: FuncionarioUpdate,
    db: AsyncSession = Depends(get_db),
    usuario_atual: CurrentUser = Depends(require_role(Role.admin)),
) -> Funcionario:
    funcionario = await _buscar_ou_404(funcionario_id, db)

    is_self = str(funcionario.id) == usuario_atual.id
    if is_self and ((dados.ativo is False) or (dados.role is not None and dados.role != Role.admin)):
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Você não pode desativar ou rebaixar sua própria conta")

    if dados.nome is not None:
        funcionario.nome = dados.nome
    if dados.role is not None:
        funcionario.role = dados.role
    if dados.ativo is not None:
        funcionario.ativo = dados.ativo

    await db.commit()
    await db.refresh(funcionario)
    return funcionario
