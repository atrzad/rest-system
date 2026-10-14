import { Suspense, lazy, useEffect, useState } from "react";
import { BrowserRouter, Route, Routes } from "react-router-dom";

import { getHealth } from "./api/endpoints";
import { AuthProvider } from "./auth/AuthContext";
import { RequireRole } from "./auth/RequireRole";
import Login from "./pages/Login";
import AdminHome from "./pages/admin/AdminHome";
import Funcionarios from "./pages/admin/Funcionarios";
import Cardapio from "./pages/admin/Cardapio";
import MesasAdmin from "./pages/admin/Mesas";
import ImprimirQR from "./pages/admin/ImprimirQR";
import EntrarMesa from "./pages/cliente/EntrarMesa";
import SelfView from "./pages/cliente/SelfView";
import SalaoHome from "./pages/salao/SalaoHome";
import MesasSalao from "./pages/salao/Mesas";
import ComandaDetalhe from "./pages/salao/ComandaDetalhe";
import CozinhaHome from "./pages/cozinha/CozinhaHome";
import KDS from "./pages/cozinha/KDS";

// Carregado sob demanda: o Recharts é pesado e só o admin usa (o cliente no celular não baixa).
const Dashboard = lazy(() => import("./pages/admin/Dashboard"));

function ApiStatus() {
  const [status, setStatus] = useState<"checking" | "ok" | "erro">("checking");

  useEffect(() => {
    getHealth()
      .then(() => setStatus("ok"))
      .catch(() => setStatus("erro"));
  }, []);

  return (
    <p
      style={{
        textAlign: "center",
        fontFamily: "sans-serif",
        color: status === "ok" ? "green" : status === "erro" ? "crimson" : "gray",
      }}
    >
      API: {status}
    </p>
  );
}

export default function App() {
  return (
    <BrowserRouter>
      <AuthProvider>
        <Routes>
          <Route path="/" element={<Login />} />
          <Route
            path="/admin"
            element={
              <RequireRole roles={["admin"]}>
                <AdminHome />
              </RequireRole>
            }
          />
          <Route
            path="/admin/funcionarios"
            element={
              <RequireRole roles={["admin"]}>
                <Funcionarios />
              </RequireRole>
            }
          />
          <Route
            path="/admin/cardapio"
            element={
              <RequireRole roles={["admin"]}>
                <Cardapio />
              </RequireRole>
            }
          />
          <Route
            path="/admin/mesas"
            element={
              <RequireRole roles={["admin"]}>
                <MesasAdmin />
              </RequireRole>
            }
          />
          <Route
            path="/admin/dashboard"
            element={
              <RequireRole roles={["admin"]}>
                <Suspense fallback={<p>Carregando...</p>}>
                  <Dashboard />
                </Suspense>
              </RequireRole>
            }
          />
          <Route
            path="/admin/mesas/imprimir"
            element={
              <RequireRole roles={["admin"]}>
                <ImprimirQR />
              </RequireRole>
            }
          />
          {/* Rotas públicas do cliente (sem login): o QR da mesa aponta para /mesa/:numero?t=TOKEN */}
          <Route path="/mesa" element={<EntrarMesa />} />
          <Route path="/mesa/:numero" element={<SelfView />} />
          <Route
            path="/salao"
            element={
              <RequireRole roles={["salao"]}>
                <SalaoHome />
              </RequireRole>
            }
          />
          <Route
            path="/salao/mesas"
            element={
              <RequireRole roles={["salao"]}>
                <MesasSalao />
              </RequireRole>
            }
          />
          <Route
            path="/salao/comandas/:comandaId"
            element={
              <RequireRole roles={["salao"]}>
                <ComandaDetalhe />
              </RequireRole>
            }
          />
          <Route
            path="/cozinha"
            element={
              <RequireRole roles={["cozinha"]}>
                <CozinhaHome />
              </RequireRole>
            }
          />
          <Route
            path="/cozinha/kds"
            element={
              <RequireRole roles={["cozinha"]}>
                <KDS />
              </RequireRole>
            }
          />
        </Routes>
        <ApiStatus />
      </AuthProvider>
    </BrowserRouter>
  );
}
