/** Ponto verde/vermelho mostrando se a tela está recebendo atualizações em tempo real. */
export default function Conexao({ conectado }: { conectado: boolean }) {
  return (
    <span className={`conexao${conectado ? " ligada" : ""}`} role="status">
      {conectado ? "Ao vivo" : "Reconectando..."}
    </span>
  );
}
