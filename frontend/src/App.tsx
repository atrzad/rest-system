import { useEffect, useState } from "react";
import { BrowserRouter, Route, Routes } from "react-router-dom";

import { getHealth } from "./api/endpoints";
import Login from "./pages/Login";

function ApiStatus() {
  const [status, setStatus] = useState<"checking" | "ok" | "erro">("checking");

  useEffect(() => {
    getHealth()
      .then(() => setStatus("ok"))
      .catch(() => setStatus("erro"));
  }, []);

  return (
    <p style={{ textAlign: "center", fontFamily: "sans-serif", color: status === "ok" ? "green" : status === "erro" ? "crimson" : "gray" }}>
      API: {status}
    </p>
  );
}

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Login />} />
      </Routes>
      <ApiStatus />
    </BrowserRouter>
  );
}
