import { Suspense, lazy } from "react";
import { BrowserRouter, Navigate, Route, Routes } from "react-router-dom";

import { AuthProvider } from "./auth/AuthContext";
import { RequireRole } from "./auth/RequireRole";
import { LayoutAdmin, LayoutCozinha, LayoutSalao } from "./components/layout/Layouts";
import { Carregando } from "./components/ui/Estados";
import Login from "./pages/Login";

// Cada tela é baixada só quando alguém abre: o cliente que lê o QR não baixa o código do admin,
// e o Recharts (pesado) fica só no dashboard.
const Dashboard = lazy(() => import("./pages/admin/Dashboard"));
const Funcionarios = lazy(() => import("./pages/admin/Funcionarios"));
const Cardapio = lazy(() => import("./pages/admin/Cardapio"));
const MesasAdmin = lazy(() => import("./pages/admin/Mesas"));
const ImprimirQR = lazy(() => import("./pages/admin/ImprimirQR"));
const EntrarMesa = lazy(() => import("./pages/cliente/EntrarMesa"));
const SelfView = lazy(() => import("./pages/cliente/SelfView"));
const MesasSalao = lazy(() => import("./pages/salao/Mesas"));
const ComandaDetalhe = lazy(() => import("./pages/salao/ComandaDetalhe"));
const KDS = lazy(() => import("./pages/cozinha/KDS"));

export default function App() {
  return (
    <BrowserRouter>
      <AuthProvider>
        <Suspense fallback={<Carregando />}>
          <Routes>
            <Route path="/" element={<Login />} />

            <Route
              path="/admin"
              element={
                <RequireRole roles={["admin"]}>
                  <LayoutAdmin />
                </RequireRole>
              }
            >
              <Route index element={<Navigate to="/admin/dashboard" replace />} />
              <Route path="dashboard" element={<Dashboard />} />
              <Route path="cardapio" element={<Cardapio />} />
              <Route path="mesas" element={<MesasAdmin />} />
              <Route path="funcionarios" element={<Funcionarios />} />
            </Route>
            {/* Folha de impressão: fora do layout, sem cabeçalho nem menu. */}
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
                  <LayoutSalao />
                </RequireRole>
              }
            >
              <Route index element={<Navigate to="/salao/mesas" replace />} />
              <Route path="mesas" element={<MesasSalao />} />
              <Route path="comandas/:comandaId" element={<ComandaDetalhe />} />
            </Route>

            <Route
              path="/cozinha"
              element={
                <RequireRole roles={["cozinha"]}>
                  <LayoutCozinha />
                </RequireRole>
              }
            >
              <Route index element={<Navigate to="/cozinha/kds" replace />} />
              <Route path="kds" element={<KDS />} />
            </Route>

            <Route path="*" element={<Navigate to="/" replace />} />
          </Routes>
        </Suspense>
      </AuthProvider>
    </BrowserRouter>
  );
}
