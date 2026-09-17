import { useAuth } from "../../auth/AuthContext";

export default function SalaoHome() {
  const { user, logout } = useAuth();

  return (
    <main style={{ maxWidth: 480, margin: "10vh auto", fontFamily: "sans-serif" }}>
      <h1>Salão</h1>
      <p>Bem-vindo, {user?.nome}.</p>
      <button onClick={logout}>Sair</button>
    </main>
  );
}
