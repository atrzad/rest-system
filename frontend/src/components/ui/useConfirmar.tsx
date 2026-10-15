import { useCallback, useState } from "react";
import type { ReactNode } from "react";

import Dialogo from "./Dialogo";

export interface OpcoesConfirmar {
  titulo: string;
  mensagem: ReactNode;
  /** Texto do botão que confirma (ex.: "Cancelar pedido"). */
  confirmar: string;
  /** Texto do botão que desiste. Padrão: "Voltar". */
  voltar?: string;
  /** Ação que apaga ou desfaz algo: botão vermelho. */
  destrutivo?: boolean;
}

interface Pendente extends OpcoesConfirmar {
  responder: (sim: boolean) => void;
}

/**
 * Substitui o confirm() do navegador por um diálogo do app.
 *   const [dialogoConfirmar, confirmar] = useConfirmar();
 *   if (!(await confirmar({ titulo, mensagem, confirmar: "Cancelar pedido", destrutivo: true }))) return;
 *   ...e renderizar {dialogoConfirmar} em algum lugar da tela.
 * O foco começa em "Voltar", para um toque sem querer não confirmar nada.
 */
export function useConfirmar(): [ReactNode, (opcoes: OpcoesConfirmar) => Promise<boolean>] {
  const [pendente, setPendente] = useState<Pendente | null>(null);

  const confirmar = useCallback(
    (opcoes: OpcoesConfirmar) => new Promise<boolean>((responder) => setPendente({ ...opcoes, responder })),
    [],
  );

  function responder(sim: boolean) {
    pendente?.responder(sim);
    setPendente(null);
  }

  const dialogo = pendente && (
    <Dialogo
      aberto
      titulo={pendente.titulo}
      aoFechar={() => responder(false)}
      acoes={
        <>
          <button type="button" onClick={() => responder(false)} autoFocus>
            {pendente.voltar ?? "Voltar"}
          </button>
          <button
            type="button"
            className={pendente.destrutivo ? "perigo-cheio" : "primario"}
            onClick={() => responder(true)}
          >
            {pendente.confirmar}
          </button>
        </>
      }
    >
      <div>{pendente.mensagem}</div>
    </Dialogo>
  );

  return [dialogo, confirmar];
}
