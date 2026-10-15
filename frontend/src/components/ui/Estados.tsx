import type { ReactNode } from "react";

/** Telas de "carregando", "nada aqui ainda" e "não deu para carregar", iguais em todo o app. */

export function Carregando({ texto = "Carregando..." }: { texto?: string }) {
  return (
    <div className="estado" role="status">
      <span className="girando" aria-hidden="true" />
      {texto}
    </div>
  );
}

export function Vazio({ titulo, children }: { titulo: string; children?: ReactNode }) {
  return (
    <div className="estado">
      <strong>{titulo}</strong>
      {children}
    </div>
  );
}

/** Erro com botão de tentar de novo. Use dentro da tela quando os dados não vieram. */
export function ErroAoCarregar({ mensagem, aoTentarDeNovo }: { mensagem: string; aoTentarDeNovo?: () => void }) {
  return (
    <div className="alerta-caixa erro" role="alert">
      <span>{mensagem}</span>
      {aoTentarDeNovo && (
        <button type="button" onClick={aoTentarDeNovo}>
          Tentar de novo
        </button>
      )}
    </div>
  );
}
