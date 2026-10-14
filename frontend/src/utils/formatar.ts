/** Formata um valor em reais ("12.5" ou 12.5 → "R$ 12,50"). */
export function formatarReais(valor: string | number): string {
  return Number(valor).toLocaleString("pt-BR", { style: "currency", currency: "BRL" });
}

export const NOME_STATUS_PEDIDO: Record<string, string> = {
  recebido: "Recebido",
  em_preparo: "Em preparo",
  pronto: "Pronto",
  entregue: "Entregue",
  cancelado: "Cancelado",
};
