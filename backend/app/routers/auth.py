import logging
import time
from collections import deque

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

# Limite de tentativas erradas por e-mail (o site é público). Em memória: zera se o serviço reiniciar,
# o que basta para frear quem tenta adivinhar senha. Por e-mail e não por IP porque, atrás do
# proxy do Tailscale, todo mundo chega como 127.0.0.1.
MAX_FALHAS = 5
JANELA_SEGUNDOS = 15 * 60
MAX_EMAILS_GUARDADOS = 10_000
_falhas: dict[str, deque[float]] = {}


def _falhas_recentes(email: str, agora: float) -> deque[float]:
    falhas = _falhas.get(email, deque())
    while falhas and agora - falhas[0] > JANELA_SEGUNDOS:
        falhas.popleft()
    return falhas


def _registrar_falha(email: str, falhas: deque[float], agora: float) -> None:
    falhas.append(agora)
    _falhas[email] = falhas
    if len(_falhas) > MAX_EMAILS_GUARDADOS:
        # Alguém tentando muitos e-mails diferentes: descarta os que já saíram da janela.
        for chave in [k for k, v in _falhas.items() if agora - v[-1] > JANELA_SEGUNDOS]:
            del _falhas[chave]


@router.post("/login", response_model=LoginResponse)
async def login(dados: LoginRequest, db: AsyncSession = Depends(get_db)) -> LoginResponse:
    email = dados.email.lower()
    agora = time.monotonic()
    falhas = _falhas_recentes(email, agora)
    if len(falhas) >= MAX_FALHAS:
        minutos = int((JANELA_SEGUNDOS - (agora - falhas[0])) // 60) + 1
        logger.warning("Login bloqueado por excesso de tentativas: %s", email)
        raise HTTPException(
            status.HTTP_429_TOO_MANY_REQUESTS, f"Muitas tentativas erradas. Tente de novo em {minutos} min."
        )

    resultado = await db.execute(select(Funcionario).where(Funcionario.email == dados.email))
    funcionario = resultado.scalar_one_or_none()

    if funcionario is None or not funcionario.ativo or not verificar_senha(dados.senha, funcionario.senha_hash):
        _registrar_falha(email, falhas, agora)
        logger.warning("Tentativa de login inválida para %s", dados.email)
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "E-mail ou senha inválidos")

    _falhas.pop(email, None)
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
