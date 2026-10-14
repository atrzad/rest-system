import { Link } from "react-router-dom";

import { useAuth } from "../../auth/AuthContext";

export default function CozinhaHome() {
  const { user, logout } = useAuth();

  return (
    <main className="pagina">
      <h1>Cozinha</h1>
      <p>Bem-vindo, {user?.nome}.</p>
      <p>
        <Link to="/cozinha/kds">Abrir KDS</Link>
      </p>
      <button onClick={logout}>Sair</button>
    </main>
  );
}
