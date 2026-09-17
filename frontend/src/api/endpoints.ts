import { apiFetch } from "./client";
import type { Role } from "../types/auth";

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
