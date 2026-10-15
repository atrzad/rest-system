import { Suspense } from "react";
import { NavLink, Outlet } from "react-router-dom";

import { useAuth } from "../../auth/AuthContext";
import ChamadosBanner from "../ChamadosBanner";
import { Carregando } from "../ui/Estados";

/** Barra do topo comum aos três perfis: nome do sistema, perfil, quem está logado e Sair. */
function CabecalhoApp({ perfil }: { perfil: string }) {
  const { user, logout } = useAuth();
  return (
    <header className="app-cabecalho">
      <div className="app-marca">
        <strong>Rest System</strong>
        <span>{perfil}</span>
      </div>
      <div className="app-conta">
        <span className="nome" title={user?.nome}>
          {user?.nome}
        </span>
        <button type="button" className="terciario" onClick={logout}>
          Sair
        </button>
      </div>
    </header>
  );
}

/** Tela da rota atual; enquanto ela é baixada, o cabeçalho e o menu continuam na tela. */
function ConteudoDaRota() {
  return (
    <Suspense fallback={<Carregando />}>
      <Outlet />
    </Suspense>
  );
}

/** Garçom: cabeçalho + faixa de chamados das mesas (uma só, em todas as telas do salão). */
export function LayoutSalao() {
  return (
    <>
      <div className="app-topo">
        <CabecalhoApp perfil="Salão" />
        <ChamadosBanner />
      </div>
      <ConteudoDaRota />
    </>
  );
}

export function LayoutCozinha() {
  return (
    <>
      <div className="app-topo">
        <CabecalhoApp perfil="Cozinha" />
      </div>
      <ConteudoDaRota />
    </>
  );
}

const MENU_ADMIN = [
  { para: "/admin/dashboard", rotulo: "Vendas" },
  { para: "/admin/cardapio", rotulo: "Cardápio" },
  { para: "/admin/mesas", rotulo: "Mesas" },
  { para: "/admin/funcionarios", rotulo: "Funcionários" },
];

/** Admin: menu lateral no desktop; no celular os mesmos atalhos ficam numa faixa embaixo do cabeçalho. */
export function LayoutAdmin() {
  return (
    <>
      <div className="app-topo">
        <CabecalhoApp perfil="Administração" />
      </div>
      <div className="admin">
        <nav className="admin-menu" aria-label="Administração">
          {MENU_ADMIN.map((item) => (
            <NavLink key={item.para} to={item.para} end={item.para === "/admin/mesas"}>
              {item.rotulo}
            </NavLink>
          ))}
        </nav>
        <div className="admin-conteudo">
          <ConteudoDaRota />
        </div>
      </div>
    </>
  );
}
