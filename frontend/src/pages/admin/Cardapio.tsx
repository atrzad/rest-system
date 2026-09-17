import { useEffect, useState } from "react";
import type { FormEvent } from "react";
import { Link } from "react-router-dom";

import { ApiError } from "../../api/client";
import { atualizarProduto, criarProduto, listProdutos } from "../../api/endpoints";
import type { Produto } from "../../types/domain";

export default function Cardapio() {
  const [produtos, setProdutos] = useState<Produto[]>([]);
  const [carregando, setCarregando] = useState(true);
  const [erro, setErro] = useState<string | null>(null);

  const [nome, setNome] = useState("");
  const [categoria, setCategoria] = useState("");
  const [preco, setPreco] = useState("");
  const [criando, setCriando] = useState(false);

  async function carregar() {
    setCarregando(true);
    try {
      setProdutos(await listProdutos());
      setErro(null);
    } catch (err) {
      setErro(err instanceof ApiError ? err.message : "Erro ao carregar cardápio");
    } finally {
      setCarregando(false);
    }
  }

  useEffect(() => {
    carregar();
  }, []);

  async function handleCriar(event: FormEvent) {
    event.preventDefault();
    setCriando(true);
    setErro(null);
    try {
      await criarProduto({ nome, categoria, preco, disponivel: true });
      setNome("");
      setCategoria("");
      setPreco("");
      await carregar();
    } catch (err) {
      setErro(err instanceof ApiError ? err.message : "Erro ao criar produto");
    } finally {
      setCriando(false);
    }
  }

  async function handleToggleDisponivel(produto: Produto) {
    try {
      await atualizarProduto(produto.id, { disponivel: !produto.disponivel });
      await carregar();
    } catch (err) {
      setErro(err instanceof ApiError ? err.message : "Erro ao atualizar produto");
    }
  }

  return (
    <main style={{ maxWidth: 720, margin: "5vh auto", fontFamily: "sans-serif" }}>
      <p>
        <Link to="/admin">← voltar</Link>
      </p>
      <h1>Cardápio</h1>

      <form onSubmit={handleCriar} style={{ display: "flex", gap: 8, flexWrap: "wrap", marginBottom: 24 }}>
        <input placeholder="Nome" value={nome} onChange={(e) => setNome(e.target.value)} required />
        <input placeholder="Categoria" value={categoria} onChange={(e) => setCategoria(e.target.value)} required />
        <input
          placeholder="Preço"
          type="number"
          step="0.01"
          min="0"
          value={preco}
          onChange={(e) => setPreco(e.target.value)}
          required
        />
        <button type="submit" disabled={criando}>
          {criando ? "Criando..." : "Adicionar"}
        </button>
      </form>

      {erro && <p style={{ color: "crimson" }}>{erro}</p>}

      {carregando ? (
        <p>Carregando...</p>
      ) : (
        <table style={{ width: "100%", borderCollapse: "collapse" }}>
          <thead>
            <tr style={{ textAlign: "left", borderBottom: "1px solid #ccc" }}>
              <th>Nome</th>
              <th>Categoria</th>
              <th>Preço</th>
              <th>Disponível</th>
            </tr>
          </thead>
          <tbody>
            {produtos.map((p) => (
              <tr key={p.id} style={{ borderBottom: "1px solid #eee" }}>
                <td>{p.nome}</td>
                <td>{p.categoria}</td>
                <td>R$ {p.preco}</td>
                <td>
                  <input type="checkbox" checked={p.disponivel} onChange={() => handleToggleDisponivel(p)} />
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </main>
  );
}
