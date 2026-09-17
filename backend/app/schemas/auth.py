from pydantic import BaseModel, EmailStr

from app.models.roles import Role


class LoginRequest(BaseModel):
    email: EmailStr
    senha: str


class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    role: Role
    nome: str


class CurrentUser(BaseModel):
    id: str
    nome: str
    email: str
    role: Role
