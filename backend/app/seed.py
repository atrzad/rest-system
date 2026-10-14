"""Cria um funcionário inicial (ex: o primeiro admin). Uso:

    .venv/bin/python -m app.seed --nome "Admin" --email admin@seudominio.com --role admin

Sem --senha, a senha é lida da entrada padrão (não fica no histórico do shell nem no `ps`):

    printf '%s' "$SENHA" | .venv/bin/python -m app.seed --nome "Admin" --email admin@seudominio.com
"""

import argparse
import asyncio
import getpass
import sys

from sqlalchemy import select

from app.auth.security import hash_senha
from app.db.session import SessionLocal
from app.models.funcionario import Funcionario
from app.models.roles import Role


async def seed(nome: str, email: str, senha: str, role: Role) -> None:
    async with SessionLocal() as db:
        existente = await db.execute(select(Funcionario).where(Funcionario.email == email))
        if existente.scalar_one_or_none() is not None:
            print(f"Já existe um funcionário com o e-mail {email}, nada a fazer.")
            return

        funcionario = Funcionario(nome=nome, email=email, senha_hash=hash_senha(senha), role=role)
        db.add(funcionario)
        await db.commit()
        print(f"Funcionário criado: {email} (role={role.value})")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--nome", required=True)
    parser.add_argument("--email", required=True)
    parser.add_argument("--senha", help="evite: prefira mandar pela entrada padrão")
    parser.add_argument("--role", choices=[r.value for r in Role], default=Role.admin.value)
    args = parser.parse_args()

    senha = args.senha
    if senha is None:
        senha = getpass.getpass("Senha: ") if sys.stdin.isatty() else sys.stdin.readline().rstrip("\n")
    if len(senha) < 8:
        sys.exit("Senha muito curta (mínimo 8 caracteres).")

    asyncio.run(seed(args.nome, args.email, senha, Role(args.role)))
