import { Link } from "react-router-dom";

import { useAuth } from "../../auth/AuthContext";
import ChamadosBanner from "../../components/ChamadosBanner";

export default function SalaoHome() {
  const { user, logout } = useAuth();

  return (
    <main className="pagina">
      <ChamadosBanner />
      <h1>Salão</h1>
      <p>Bem-vindo, {user?.nome}.</p>
      <p>
        <Link to="/salao/mesas">Mesas</Link>
      </p>
      <button onClick={logout}>Sair</button>
    </main>
  );
}
