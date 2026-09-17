import enum


class Role(str, enum.Enum):
    admin = "admin"
    salao = "salao"
    cozinha = "cozinha"
