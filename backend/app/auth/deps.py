from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.auth.security import decodificar_access_token
from app.models.roles import Role
from app.schemas.auth import CurrentUser

bearer_scheme = HTTPBearer(auto_error=False)


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
) -> CurrentUser:
    if credentials is None:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Token não informado")

    try:
        payload = decodificar_access_token(credentials.credentials)
    except ValueError as exc:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, str(exc)) from exc

    return CurrentUser(
        id=payload["sub"],
        nome=payload.get("nome", ""),
        email=payload.get("email", ""),
        role=Role(payload["role"]),
    )


def require_role(*roles: Role):
    def dependency(user: CurrentUser = Depends(get_current_user)) -> CurrentUser:
        if user.role not in roles:
            raise HTTPException(status.HTTP_403_FORBIDDEN, "Acesso não permitido para este perfil")
        return user

    return dependency
