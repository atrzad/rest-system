import { Link } from "react-router-dom";

import { useAuth } from "../../auth/AuthContext";

export default function AdminHome() {
  const { user, logout } = useAuth();

  return (
    <main style={{ maxWidth: 480, margin: "10vh auto", fontFamily: "sans-serif" }}>
      <h1>Painel admin</h1>
      <p>Bem-vindo, {user?.nome}.</p>
      <p>
        <Link to="/admin/funcionarios">Funcionários</Link>
      </p>
      <p>
        <Link to="/admin/cardapio">Cardápio</Link>
      </p>
      <p>
        <Link to="/admin/mesas">Mesas</Link>
      </p>
      <button onClick={logout}>Sair</button>
    </main>
  );
}
