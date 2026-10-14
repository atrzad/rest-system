import { useEffect, useState } from "react";
import { QRCodeSVG } from "qrcode.react";
import { Link } from "react-router-dom";

import { ApiError } from "../../api/client";
import { listMesas } from "../../api/endpoints";
import type { Mesa } from "../../types/domain";

/** Folha com o QR de cada mesa ativa + número + código para digitar, pronta para imprimir. */
export default function ImprimirQR() {
  const [mesas, setMesas] = useState<Mesa[]>([]);
  const [erro, setErro] = useState<string | null>(null);

  useEffect(() => {
    listMesas()
      .then((lista) => setMesas(lista.filter((m) => m.ativa)))
      .catch((err) => setErro(err instanceof ApiError ? err.message : "Erro ao carregar mesas"));
  }, []);

  return (
    <main style={{ padding: 16, fontFamily: "sans-serif", color: "#000", background: "#fff" }}>
      <style>{"@media print { .nao-imprimir { display: none !important; } #root { border: none; } }"}</style>
      <div className="nao-imprimir" style={{ display: "flex", gap: 12, alignItems: "center", marginBottom: 16 }}>
        <Link to="/admin/mesas">← voltar</Link>
        <button onClick={() => window.print()}>Imprimir</button>
      </div>
      {erro && <p style={{ color: "crimson" }}>{erro}</p>}
      <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(220px, 1fr))", gap: 16 }}>
        {mesas.map((mesa) => (
          <div
            key={mesa.id}
            style={{
              border: "2px dashed #999",
              borderRadius: 8,
              padding: 12,
              textAlign: "center",
              breakInside: "avoid",
            }}
          >
            <h2 style={{ margin: "0 0 8px", color: "#000" }}>Mesa {mesa.numero}</h2>
            {mesa.url_qr && <QRCodeSVG value={mesa.url_qr} size={170} marginSize={2} />}
            <p style={{ margin: "8px 0 0", fontSize: 13 }}>Aponte a câmera para ver seus pedidos e chamar o garçom</p>
            <p style={{ margin: "4px 0 0", fontSize: 13 }}>
              Sem câmera? Acesse <strong>/mesa</strong> e digite o código
            </p>
            <p style={{ margin: "4px 0 0", fontSize: 22, letterSpacing: 4 }}>
              <strong>{mesa.token}</strong>
            </p>
          </div>
        ))}
      </div>
    </main>
  );
}
