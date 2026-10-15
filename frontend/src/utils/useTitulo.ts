import { useEffect } from "react";

/** Título da aba do navegador: "Mesas · Rest System". */
export function useTitulo(titulo: string) {
  useEffect(() => {
    document.title = titulo ? `${titulo} · Rest System` : "Rest System";
  }, [titulo]);
}
