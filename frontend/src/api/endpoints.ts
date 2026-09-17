import { apiFetch } from "./client";
import type { Funcionario, Role } from "../types/auth";

export interface HealthResponse {
  status: string;
}

export function getHealth(): Promise<HealthResponse> {
  return apiFetch<HealthResponse>("/health");
}

export interface LoginResponse {
  access_token: string;
  token_type: string;
  role: Role;
  nome: string;
}

export function login(email: string, senha: string): Promise<LoginResponse> {
  return apiFetch<LoginResponse>("/auth/login", {
    method: "POST",
    body: JSON.stringify({ email, senha }),
  });
}

export function listFuncionarios(): Promise<Funcionario[]> {
  return apiFetch<Funcionario[]>("/funcionarios");
}

export interface CriarFuncionarioInput {
  nome: string;
  email: string;
  senha: string;
  role: Role;
}

export function criarFuncionario(dados: CriarFuncionarioInput): Promise<Funcionario> {
  return apiFetch<Funcionario>("/funcionarios", {
    method: "POST",
    body: JSON.stringify(dados),
  });
}

export function atualizarFuncionario(
  id: string,
  dados: Partial<Pick<Funcionario, "nome" | "role" | "ativo">>,
): Promise<Funcionario> {
  return apiFetch<Funcionario>(`/funcionarios/${id}`, {
    method: "PATCH",
    body: JSON.stringify(dados),
  });
}
