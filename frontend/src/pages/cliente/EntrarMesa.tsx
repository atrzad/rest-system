import { useState } from "react";
import type { FormEvent } from "react";
import { useNavigate } from "react-router-dom";

/** Fallback quando a câmera não lê o QR: o cliente digita o número da mesa e o código impresso. */
export default function EntrarMesa() {
  const navigate = useNavigate();
  const [numero, setNumero] = useState("");
  const [codigo, setCodigo] = useState("");

  function handleEntrar(event: FormEvent) {
    event.preventDefault();
    const t = codigo.trim().toUpperCase();
    navigate(`/mesa/${Number(numero)}?t=${encodeURIComponent(t)}&origem=manual`);
  }

  return (
    <main className="pagina" style={{ maxWidth: 360, marginTop: "8vh" }}>
      <h1>Entrar na mesa</h1>
      <p>Digite o número da mesa e o código que aparece embaixo do QR code.</p>
      <form onSubmit={handleEntrar} style={{ display: "flex", flexDirection: "column", gap: 12 }}>
        <input
          placeholder="Número da mesa"
          type="number"
          inputMode="numeric"
          min="1"
          value={numero}
          onChange={(e) => setNumero(e.target.value)}
          required
          style={{ fontSize: 20, padding: 10 }}
        />
        <input
          placeholder="Código (ex.: K7P2QX)"
          value={codigo}
          onChange={(e) => setCodigo(e.target.value)}
          autoCapitalize="characters"
          autoComplete="off"
          required
          style={{ fontSize: 20, padding: 10, textTransform: "uppercase", letterSpacing: 2 }}
        />
        <button type="submit" style={{ fontSize: 20, padding: 12 }}>
          Entrar
        </button>
      </form>
    </main>
  );
}
