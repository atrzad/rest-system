export type Role = "admin" | "salao" | "cozinha";

export interface AuthUser {
  nome: string;
  role: Role;
  token: string;
}

export interface Funcionario {
  id: string;
  nome: string;
  email: string;
  role: Role;
  ativo: boolean;
  criado_em: string;
}
