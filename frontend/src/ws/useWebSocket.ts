import { useEffect, useRef } from "react";

const WS_URL = import.meta.env.VITE_WS_URL ?? "ws://localhost:8000";

export function wsUrlParaStaff(): string | null {
  const token = localStorage.getItem("token");
  return token ? `${WS_URL}/ws?token=${encodeURIComponent(token)}` : null;
}

export function wsUrlParaMesa(numeroMesa: number): string {
  return `${WS_URL}/ws?mesa=${numeroMesa}`;
}

export interface EventoEnvelope {
  tipo: string;
  id: string;
  ocorrido_em: string;
  mesa_numero: number | null;
  comanda_id: string | null;
  payload: Record<string, unknown>;
}

/** Conecta ao WebSocket e chama onEvento a cada mensagem. Reconecta sozinho se a conexão cair. */
export function useWebSocket(url: string | null, onEvento: (evento: EventoEnvelope) => void) {
  const onEventoRef = useRef(onEvento);
  onEventoRef.current = onEvento;

  useEffect(() => {
    if (!url) return;

    let socket: WebSocket | null = null;
    let timeoutId: ReturnType<typeof setTimeout> | null = null;
    let cancelado = false;

    function conectar() {
      socket = new WebSocket(url as string);

      socket.onmessage = (event) => {
        try {
          onEventoRef.current(JSON.parse(event.data));
        } catch {
          // ignora mensagens que não sejam JSON válido
        }
      };

      socket.onclose = () => {
        if (!cancelado) {
          timeoutId = setTimeout(conectar, 2000);
        }
      };
    }

    conectar();

    return () => {
      cancelado = true;
      if (timeoutId) clearTimeout(timeoutId);
      socket?.close();
    };
  }, [url]);
}
