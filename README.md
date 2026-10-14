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

## Perfis e telas

- **Admin** (`/admin`): funcionários, cardápio, mesas (código/QR de cada mesa, gerar novo código,
  folha de impressão em `/admin/mesas/imprimir`) e **Vendas** (`/admin/dashboard`).
- **Salão** (`/salao`): mapa de mesas, comanda com carrinho, marcar entregue/cancelar, fechar conta
  com resumo e taxa de serviço de 10% opcional, faixa de chamados de garçom com som.
- **Cozinha** (`/cozinha/kds`): KDS em colunas, tempo desde o pedido (amarelo > 10 min,
  vermelho > 20 min), som em pedido novo.
- **Cliente** (público): `/mesa/:numero?t=CÓDIGO` é para onde aponta o QR da mesa; `/mesa` é a
  entrada manual (número + código impresso embaixo do QR). Mostra pedidos ao vivo, conta parcial,
  cardápio e o botão "Chamar garçom".

### QR code das mesas

Cada mesa tem um código secreto de 6 caracteres (sem 0/O/1/I) que vai no QR. Sem o código certo,
as rotas públicas da mesa respondem 404, então ninguém abre comanda ou chama garçom de fora só
trocando o número na URL. Se um QR vazar, gere um código novo pelo admin e reimprima.
O endereço dentro do QR vem de `PUBLIC_BASE_URL` no `.env`.

### Regras de negócio

- Uma mesa tem no máximo uma comanda aberta (garantido por índice no banco).
- Fechar conta exige todos os pedidos entregues ou cancelados (senão a API responde 409).
- Transições de pedido por perfil: cozinha inicia preparo, marca pronto e cancela (recebido/em
  preparo); salão marca entregue e cancela só pedido recebido; admin pode tudo.
- O dashboard usa o fuso `TIMEZONE_LOCAL` (padrão `America/Manaus`) para "hoje", "por hora" e "por dia".

## Produção (Tailscale Funnel)

No ar em **https://rest-system.tail9ff58.ts.net**. Um processo só (uvicorn na porta 3700, só
localhost) entrega a API, o WebSocket e o site. Um container Tailscale próprio
(`deploy/tailscale/`) publica esse endereço na internet via Funnel; os clientes abrem pelo QR sem
precisar de Tailscale.

- **Publicar o último commit:** `deploy/publicar.sh`. Copia o HEAD para
  `~/.local/share/rest-system/releases/`, monta o venv e o build, faz backup do banco
  (`~/.local/share/rest-system/backups/`), migra, troca o link `atual`, reinicia e confere. Se o site
  não responder, volta para a versão anterior. A pasta de desenvolvimento nunca é usada pelo
  serviço, então dá para mexer nela à vontade.
- **Configuração:** `~/.config/rest-system/producao.env` (chmod 600; modelo em
  `deploy/producao.env.example`). Banco próprio `rest_system_prod` com usuário próprio, canal Redis
  próprio, `/docs` desligado.
- **Serviço:** `systemctl --user status rest-system` / `journalctl --user -u rest-system -f`
  (unidade em `deploy/rest-system.service`, copiada para `~/.config/systemd/user/`).
- **Tailscale:** `cd deploy/tailscale && docker compose up -d`; status com
  `docker exec rest-system-tailscale tailscale funnel status`.
- Login tem limite de 5 senhas erradas por e-mail a cada 15 minutos.

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
