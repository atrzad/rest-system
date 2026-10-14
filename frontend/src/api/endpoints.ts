import { apiFetch } from "./client";
import type { Funcionario, Role } from "../types/auth";
import type { Chamado, Comanda, Conta, DashboardVendas, Mesa, MesaPublica, Pedido, PedidoStatus, Produto } from "../types/domain";

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

export function listProdutos(): Promise<Produto[]> {
  return apiFetch<Produto[]>("/produtos");
}

export function criarProduto(dados: Omit<Produto, "id">): Promise<Produto> {
  return apiFetch<Produto>("/produtos", { method: "POST", body: JSON.stringify(dados) });
}

export function atualizarProduto(id: string, dados: Partial<Omit<Produto, "id">>): Promise<Produto> {
  return apiFetch<Produto>(`/produtos/${id}`, { method: "PATCH", body: JSON.stringify(dados) });
}

export function listMesas(): Promise<Mesa[]> {
  return apiFetch<Mesa[]>("/mesas");
}

export function criarMesa(dados: { numero: number; capacidade?: number | null }): Promise<Mesa> {
  return apiFetch<Mesa>("/mesas", { method: "POST", body: JSON.stringify(dados) });
}

export function regenerarTokenMesa(id: string): Promise<Mesa> {
  return apiFetch<Mesa>(`/mesas/${id}/regenerar-token`, { method: "POST" });
}

export function listComandas(status?: "aberta" | "fechada"): Promise<Comanda[]> {
  const query = status ? `?status_filtro=${status}` : "";
  return apiFetch<Comanda[]>(`/comandas${query}`);
}

export function abrirComandaPorMesa(numero_mesa: number): Promise<Comanda> {
  return apiFetch<Comanda>("/comandas/abrir-por-mesa", {
    method: "POST",
    body: JSON.stringify({ numero_mesa }),
  });
}

export function getConta(comandaId: string, taxaServico = true): Promise<Conta> {
  return apiFetch<Conta>(`/comandas/${comandaId}/conta?taxa=${taxaServico}`);
}

export function fecharComanda(id: string, taxaServico: boolean): Promise<Comanda> {
  return apiFetch<Comanda>(`/comandas/${id}/fechar`, {
    method: "POST",
    body: JSON.stringify({ taxa_servico: taxaServico }),
  });
}

export interface CriarPedidoItemInput {
  produto_id: string;
  quantidade: number;
  observacao?: string;
}

export function criarPedido(comanda_id: string, itens: CriarPedidoItemInput[]): Promise<Pedido> {
  return apiFetch<Pedido>("/pedidos", { method: "POST", body: JSON.stringify({ comanda_id, itens }) });
}

export function listPedidos(params: { status?: PedidoStatus; comandaId?: string } = {}): Promise<Pedido[]> {
  const query = new URLSearchParams();
  if (params.status) query.set("status_filtro", params.status);
  if (params.comandaId) query.set("comanda_id", params.comandaId);
  const qs = query.toString();
  return apiFetch<Pedido[]>(`/pedidos${qs ? `?${qs}` : ""}`);
}

export function atualizarStatusPedido(id: string, status: PedidoStatus): Promise<Pedido> {
  return apiFetch<Pedido>(`/pedidos/${id}/status`, { method: "PATCH", body: JSON.stringify({ status }) });
}

export function listChamados(): Promise<Chamado[]> {
  return apiFetch<Chamado[]>("/chamados");
}

export function atenderChamado(id: string): Promise<Chamado> {
  return apiFetch<Chamado>(`/chamados/${id}/atender`, { method: "POST" });
}

// --- Rotas públicas do cliente na mesa (sem login; o token do QR vai em ?t=) ---

function rotaPublica(numero: number, token: string, sufixo = ""): string {
  return `/publico/mesas/${numero}${sufixo}?t=${encodeURIComponent(token)}`;
}

export function getMesaPublica(numero: number, token: string): Promise<MesaPublica> {
  return apiFetch<MesaPublica>(rotaPublica(numero, token));
}

export function abrirComandaPublica(
  numero: number,
  token: string,
  origem: "cliente_qr" | "cliente_manual",
): Promise<{ id: string; status: string }> {
  return apiFetch(rotaPublica(numero, token, "/comanda"), { method: "POST", body: JSON.stringify({ origem }) });
}

export function chamarGarcom(numero: number, token: string): Promise<Chamado> {
  return apiFetch<Chamado>(rotaPublica(numero, token, "/chamar-garcom"), { method: "POST" });
}

export function getContaPublica(numero: number, token: string): Promise<Conta> {
  return apiFetch<Conta>(rotaPublica(numero, token, "/conta"));
}

export function getDashboardVendas(dias: number): Promise<DashboardVendas> {
  return apiFetch<DashboardVendas>(`/dashboard/vendas?dias=${dias}`);
}
