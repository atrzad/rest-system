import { useEffect, useId, useRef } from "react";
import type { ReactNode } from "react";

interface DialogoProps {
  aberto: boolean;
  titulo: string;
  /** Chamado ao apertar Esc ou ao fechar por fora; quem usa decide o que fazer. */
  aoFechar: () => void;
  children: ReactNode;
  /** Botões do rodapé (o principal por último: fica à direita no desktop e embaixo no celular). */
  acoes?: ReactNode;
}

/**
 * Diálogo modal com o <dialog> nativo do navegador: prende o foco dentro dele, deixa o fundo
 * inerte, fecha com Esc e, ao fechar, devolve o foco para o botão que o abriu.
 * No celular aparece como folha presa embaixo da tela (ver index.css).
 */
export default function Dialogo({ aberto, titulo, aoFechar, children, acoes }: DialogoProps) {
  const ref = useRef<HTMLDialogElement>(null);
  const tituloId = useId();

  useEffect(() => {
    const dialogo = ref.current;
    if (!dialogo || !aberto) return;
    const anterior = document.activeElement as HTMLElement | null;
    if (!dialogo.open) dialogo.showModal();
    return () => {
      dialogo.close();
      anterior?.focus?.();
    };
  }, [aberto]);

  if (!aberto) return null;

  return (
    <dialog
      ref={ref}
      className="dialogo"
      aria-labelledby={tituloId}
      onCancel={(evento) => {
        // Esc: quem controla o "aberto" é o componente pai.
        evento.preventDefault();
        aoFechar();
      }}
    >
      <div className="dialogo-corpo">
        <h2 id={tituloId}>{titulo}</h2>
        {children}
      </div>
      {acoes && <div className="dialogo-acoes">{acoes}</div>}
    </dialog>
  );
}
