import { useEffect, useState } from "react";
import { BrowserRouter, Route, Routes } from "react-router-dom";

import { getHealth } from "./api/endpoints";
import { AuthProvider } from "./auth/AuthContext";
import { RequireRole } from "./auth/RequireRole";
import Login from "./pages/Login";
import AdminHome from "./pages/admin/AdminHome";
import Funcionarios from "./pages/admin/Funcionarios";
import Cardapio from "./pages/admin/Cardapio";
import MesasAdmin from "./pages/admin/Mesas";
import SalaoHome from "./pages/salao/SalaoHome";
import MesasSalao from "./pages/salao/Mesas";
import CozinhaHome from "./pages/cozinha/CozinhaHome";

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
            path="/cozinha"
            element={
              <RequireRole roles={["cozinha"]}>
                <CozinhaHome />
              </RequireRole>
            }
          />
        </Routes>
        <ApiStatus />
      </AuthProvider>
    </BrowserRouter>
  );
}
