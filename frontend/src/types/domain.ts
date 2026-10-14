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
  /** Só vem preenchido para admin (segredo do QR). */
  token: string | null;
  url_qr: string | null;
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
  subtotal: string | null;
  taxa_servico: string | null;
  total: string | null;
}

export interface ContaItem {
  produto_id: string;
  produto_nome: string;
  preco_unitario: string;
  quantidade: number;
  valor: string;
}

export interface Conta {
  comanda_id: string;
  mesa_numero: number;
  itens: ContaItem[];
  subtotal: string;
  taxa_servico: string;
  total: string;
  pedidos_pendentes: number;
}

export type PedidoStatus = "recebido" | "em_preparo" | "pronto" | "entregue" | "cancelado";

export interface PedidoItem {
  id: string;
  produto_id: string;
  produto_nome: string;
  quantidade: number;
  preco_unitario: string;
  observacao: string | null;
}

export interface Pedido {
  id: string;
  comanda_id: string;
  mesa_numero: number;
  status: PedidoStatus;
  criado_em: string;
  atualizado_em: string;
  itens: PedidoItem[];
}

export interface Chamado {
  id: string;
  mesa_numero: number;
  comanda_id: string | null;
  criado_em: string;
  atendido_em: string | null;
}

export interface ProdutoPublico {
  id: string;
  nome: string;
  categoria: string;
  preco: string;
}

export interface MesaPublica {
  numero: number;
  cardapio: ProdutoPublico[];
  comanda: { id: string; status: ComandaStatus } | null;
  pedidos: Pedido[];
  chamado_aberto: boolean;
}

export interface PontoSerie {
  rotulo: string;
  inicio: string;
  valor: string;
  itens: number;
}

export interface DashboardVendas {
  inicio: string;
  fim: string;
  fuso: string;
  faturamento: string;
  taxa_servico: string;
  comandas_fechadas: number;
  ticket_medio: string;
  comandas_abertas_agora: number;
  consumo: string;
  itens_vendidos: number;
  tempo_medio_preparo_min: number | null;
  granularidade: "hora" | "dia";
  serie: PontoSerie[];
  top_produtos: { produto_id: string; nome: string; quantidade: number; valor: string }[];
  por_categoria: { categoria: string; quantidade: number; valor: string }[];
}
