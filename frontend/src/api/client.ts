import { avisarSessaoExpirada } from "../auth/sessao";

const API_URL = import.meta.env.VITE_API_URL ?? "http://localhost:8000";

export class ApiError extends Error {
  status: number;

  constructor(status: number, message: string) {
    super(message);
    this.status = status;
  }
}

/**
 * A requisição não chegou a ter resposta (sem internet, servidor fora do ar, conexão caiu no meio).
 * Num envio, isso quer dizer "não sei se chegou": o servidor pode ter gravado antes de a conexão cair.
 */
export class ErroDeRede extends ApiError {
  constructor() {
    super(0, "Sem conexão com o servidor. Verifique a internet e tente de novo.");
  }
}

function authHeader(): Record<string, string> {
  const token = localStorage.getItem("token");
  return token ? { Authorization: `Bearer ${token}` } : {};
}

export async function apiFetch<T>(path: string, options: RequestInit = {}): Promise<T> {
  const auth = authHeader();
  let response: Response;
  try {
    response = await fetch(`${API_URL}${path}`, {
      ...options,
      headers: {
        "Content-Type": "application/json",
        ...auth,
        ...options.headers,
      },
    });
  } catch {
    throw new ErroDeRede();
  }

  if (!response.ok) {
    // Token vencido ou revogado: o AuthContext leva de volta ao login (o login em si não conta).
    if (response.status === 401 && auth.Authorization && !path.startsWith("/auth/")) {
      avisarSessaoExpirada();
    }
    const body = await response.text();
    let message = body || response.statusText;
    try {
      const parsed = JSON.parse(body);
      if (typeof parsed.detail === "string") message = parsed.detail;
    } catch {
      // corpo não era JSON, mantém o texto cru
    }
    throw new ApiError(response.status, message);
  }

  if (response.status === 204) {
    return undefined as T;
  }

  return (await response.json()) as T;
}
