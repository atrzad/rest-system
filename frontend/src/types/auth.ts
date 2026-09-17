export type Role = "admin" | "salao" | "cozinha";

export interface AuthUser {
  nome: string;
  role: Role;
  token: string;
}
