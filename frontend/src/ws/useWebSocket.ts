import { useEffect, useRef, useState } from "react";

// Em dev aponta para o uvicorn (VITE_WS_URL no .env.local); no build de produção fica vazio e
// usa o mesmo endereço do site (wss:// atrás do HTTPS do Tailscale).
const WS_URL =
  import.meta.env.VITE_WS_URL || `${window.location.protocol === "https:" ? "wss" : "ws"}://${window.location.host}`;

export function wsUrlParaStaff(): string | null {
  const token = localStorage.getItem("token");
  return token ? `${WS_URL}/ws?token=${encodeURIComponent(token)}` : null;
}

export function wsUrlParaMesa(numeroMesa: number, token: string): string {
  return `${WS_URL}/ws?mesa=${numeroMesa}&t=${encodeURIComponent(token)}`;
}

export interface EventoEnvelope {
  tipo: string;
  id: string;
  ocorrido_em: string;
  mesa_numero: number | null;
  comanda_id: string | null;
  payload: Record<string, unknown>;
}

/**
 * Conecta ao WebSocket e chama onEvento a cada mensagem. Reconecta sozinho se a conexão cair.
 * Devolve se está conectado agora (para o indicador de tempo real nas telas).
 * Ao reconectar, chama onReconectar: eventos perdidos enquanto estava fora não voltam, então a tela recarrega.
 */
export function useWebSocket(
  url: string | null,
  onEvento: (evento: EventoEnvelope) => void,
  onReconectar?: () => void,
): boolean {
  const onEventoRef = useRef(onEvento);
  const onReconectarRef = useRef(onReconectar);
  const [conectado, setConectado] = useState(false);

  useEffect(() => {
    onEventoRef.current = onEvento;
    onReconectarRef.current = onReconectar;
  });

  useEffect(() => {
    if (!url) return;

    let socket: WebSocket | null = null;
    let timeoutId: ReturnType<typeof setTimeout> | null = null;
    let cancelado = false;
    let jaConectou = false;

    function conectar() {
      socket = new WebSocket(url as string);

      socket.onopen = () => {
        setConectado(true);
        if (jaConectou) onReconectarRef.current?.();
        jaConectou = true;
      };

      socket.onmessage = (event) => {
        try {
          onEventoRef.current(JSON.parse(event.data));
        } catch {
          // ignora mensagens que não sejam JSON válido
        }
      };

      socket.onclose = () => {
        setConectado(false);
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

  return conectado;
}
