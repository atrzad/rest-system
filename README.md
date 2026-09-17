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

Para criar o primeiro admin:

```bash
.venv/bin/python -m app.seed --nome "Admin" --email admin@seudominio.com --senha "..." --role admin
```

(Use um domínio de e-mail "real" — `.local`/`.test`/`.example` são rejeitados pelo
validador de e-mail por serem domínios reservados.)

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

## Logs internos

Eventos de negócio (login, abertura/fechamento de comanda, pedidos) e exceções não
tratadas ("bugs") são gravados na tabela `log_entry` do Postgres — mensagens/contextos
grandes (ex: tracebacks) são comprimidos com gzip antes de salvar. **Não existe nenhum
endpoint HTTP** para consultar isso; é acesso só de quem tem SSH/root no servidor:

```bash
cd backend
.venv/bin/python -m app.scripts.ler_logs                    # últimos 50 logs
.venv/bin/python -m app.scripts.ler_logs --nivel ERROR --limite 100
```

Retenção não é automática ainda (sem infra de cron neste momento) — para limpar logs
antigos manualmente: `DELETE FROM log_entry WHERE criado_em < now() - interval '30 days';`
