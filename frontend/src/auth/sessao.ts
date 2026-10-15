// Sessão vencida: o token JWT dura algumas horas (JWT_EXPIRE_MINUTES no servidor). Quando vence,
// a API responde 401 e o WebSocket é recusado. Em vez de deixar a tela quebrada em "Reconectando...",
// o app volta para o login com um aviso.

export const EVENTO_SESSAO_EXPIRADA = "rest-system:sessao-expirada";

export function avisarSessaoExpirada() {
  window.dispatchEvent(new Event(EVENTO_SESSAO_EXPIRADA));
}

/** Momento (ms desde 1970) em que o token vence, lido do campo "exp" do JWT. Null se não der para ler. */
export function expiracaoDoToken(token: string): number | null {
  try {
    const base64 = token.split(".")[1].replace(/-/g, "+").replace(/_/g, "/");
    const payload = JSON.parse(atob(base64));
    return typeof payload.exp === "number" ? payload.exp * 1000 : null;
  } catch {
    return null;
  }
}
