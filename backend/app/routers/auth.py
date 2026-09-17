import logging

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.deps import get_current_user
from app.auth.security import criar_access_token, verificar_senha
from app.db.session import get_db
from app.models.funcionario import Funcionario
from app.schemas.auth import CurrentUser, LoginRequest, LoginResponse

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login", response_model=LoginResponse)
async def login(dados: LoginRequest, db: AsyncSession = Depends(get_db)) -> LoginResponse:
    resultado = await db.execute(select(Funcionario).where(Funcionario.email == dados.email))
    funcionario = resultado.scalar_one_or_none()

    if funcionario is None or not funcionario.ativo or not verificar_senha(dados.senha, funcionario.senha_hash):
        logger.warning("Tentativa de login inválida para %s", dados.email)
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "E-mail ou senha inválidos")

    logger.info("Login bem-sucedido: %s (role=%s)", funcionario.email, funcionario.role.value)
    token = criar_access_token(
        sub=str(funcionario.id),
        role=funcionario.role.value,
        nome=funcionario.nome,
        email=funcionario.email,
    )
    return LoginResponse(access_token=token, role=funcionario.role, nome=funcionario.nome)


@router.get("/me", response_model=CurrentUser)
async def me(user: CurrentUser = Depends(get_current_user)) -> CurrentUser:
    return user
