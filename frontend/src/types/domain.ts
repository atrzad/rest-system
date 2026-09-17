export interface Produto {
  id: string;
  nome: string;
  categoria: string;
  preco: string;
  disponivel: boolean;
}

export interface Mesa {
  id: string;
  numero: number;
  capacidade: number | null;
  ativa: boolean;
}

export type ComandaStatus = "aberta" | "fechada";
export type OrigemAbertura = "cliente_qr" | "cliente_manual" | "garcom";

export interface Comanda {
  id: string;
  mesa_id: string;
  mesa_numero: number;
  status: ComandaStatus;
  aberta_por: OrigemAbertura;
  aberta_em: string;
  fechada_em: string | null;
  total: string | null;
}
