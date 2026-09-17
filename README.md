# Rest System

Sistema de comandas + KDS (Kitchen Display System) orientado a eventos, com 3 perfis
(admin, salão, cozinha), comandas via QR code fixo por mesa (com fallback manual) e
dashboard de vendas em tempo real.

Plano de implementação completo em `docs/`. Arquitetura: FastAPI (async) + PostgreSQL +
Redis Pub/Sub + WebSockets no backend; React + TypeScript (Vite) no frontend.

## Rodando em desenvolvimento

Pré-requisito: Docker rodando (Postgres + Redis).

```bash
cp .env.example .env
docker compose up -d
```

### Backend

```bash
cd backend
python3 -m venv .venv
.venv/bin/pip install -e .
.venv/bin/uvicorn app.main:app --reload --port 8000
```

Testa em `http://localhost:8000/health`.

### Frontend

```bash
cd frontend
cp .env.example .env.local
npm install
npm run dev
```

Abre em `http://localhost:5173`.

## Estrutura

- `backend/app/` — FastAPI: `models/`, `routers/`, `events/` (bus Redis), `ws/` (WebSocket
  fan-out), `services/`.
- `frontend/src/` — React: `pages/admin`, `pages/salao`, `pages/cozinha`, `pages/cliente`.
- `docs/eventos.md` — catálogo dos eventos de domínio do sistema.
