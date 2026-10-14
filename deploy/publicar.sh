#!/usr/bin/env bash
# Publica o último commit (HEAD) do Rest System em produção:
#   1. copia o código commitado para ~/.local/share/rest-system/releases/<commit>-<data>
#   2. cria o venv e faz o build do frontend nessa cópia
#   3. faz backup do banco de produção e roda as migrações
#   4. aponta ~/.local/share/rest-system/atual para a cópia nova e reinicia o serviço
#   5. confere se o site respondeu; se não, volta para a versão anterior
#
# Mudanças não commitadas NÃO vão para produção (é publicado o HEAD).
# Uso: deploy/publicar.sh
set -euo pipefail

REPO="$(cd "$(dirname "$0")/.." && pwd)"
DESTINO="${DESTINO:-$HOME/.local/share/rest-system}"
ENV_PROD="${ENV_PROD:-$HOME/.config/rest-system/producao.env}"
SERVICO="rest-system"
PORTA=3700
MANTER_RELEASES=3

falhar() { echo "✗ $*" >&2; exit 1; }
passo() { echo "→ $*"; }

# docker sem relogar depois de entrar no grupo docker: cai para `sg docker`.
docker_() {
  if docker info >/dev/null 2>&1; then docker "$@"; else sg docker -c "$(printf '%q ' docker "$@")"; fi
}

[[ -f "$ENV_PROD" ]] || falhar "Falta $ENV_PROD (modelo em deploy/producao.env.example)"
[[ "$(stat -c %a "$ENV_PROD")" == "600" ]] || falhar "$ENV_PROD precisa de chmod 600 (tem segredos)"
if [[ -n "$(git -C "$REPO" status --porcelain)" ]]; then
  echo "! Há mudanças não commitadas; elas NÃO serão publicadas (só o HEAD)."
fi

COMMIT="$(git -C "$REPO" rev-parse --short HEAD)"
NOVA="$DESTINO/releases/$COMMIT-$(date +%Y%m%d-%H%M%S)"
ANTERIOR="$(readlink -f "$DESTINO/atual" 2>/dev/null || true)"

passo "Copiando o commit $COMMIT para $NOVA"
mkdir -p "$NOVA" "$DESTINO/backups"
git -C "$REPO" archive HEAD | tar -x -C "$NOVA"

passo "Backend: venv e dependências"
python3 -m venv "$NOVA/backend/.venv"
"$NOVA/backend/.venv/bin/pip" install -q --upgrade pip
"$NOVA/backend/.venv/bin/pip" install -q -e "$NOVA/backend"

passo "Frontend: build de produção"
(cd "$NOVA/frontend" && npm ci --silent --no-audit --no-fund && npm run build --silent >/dev/null && rm -rf node_modules)
[[ -f "$NOVA/frontend/dist/index.html" ]] || falhar "build do frontend não gerou dist/index.html"

# Variáveis de produção (DATABASE_URL etc.) para backup e migração.
set -a; source "$ENV_PROD"; set +a
BANCO="${DATABASE_URL##*/}"
USUARIO_BANCO="$(sed -E 's#^[^/]*//([^:]+):.*#\1#' <<<"$DATABASE_URL")"

passo "Backup do banco $BANCO"
BACKUP="$DESTINO/backups/$BANCO-$(date +%Y%m%d-%H%M%S)-antes-de-$COMMIT.sql.gz"
(cd "$REPO" && docker_ compose exec -T postgres pg_dump -U "$USUARIO_BANCO" "$BANCO") | gzip >"$BACKUP"
chmod 600 "$BACKUP"
ls -1t "$DESTINO"/backups/*.sql.gz | tail -n +15 | xargs -r rm --

passo "Migrações"
(cd "$NOVA/backend" && .venv/bin/alembic upgrade head)

passo "Trocando para a versão nova e reiniciando o serviço"
ln -sfn "$NOVA" "$DESTINO/atual"
systemctl --user restart "$SERVICO"

passo "Conferindo se o site respondeu"
for _ in $(seq 1 20); do
  if curl -fsS "http://127.0.0.1:$PORTA/health" >/dev/null 2>&1 \
    && curl -fsS "http://127.0.0.1:$PORTA/" | grep -q '<div id="root">'; then
    echo "✓ Publicado: $COMMIT  ($PUBLIC_BASE_URL)"
    ls -1dt "$DESTINO"/releases/*/ | tail -n +$((MANTER_RELEASES + 1)) | xargs -r rm -rf --
    exit 0
  fi
  sleep 1
done

echo "✗ O serviço não respondeu. Últimas linhas do log:" >&2
journalctl --user -u "$SERVICO" -n 30 --no-pager >&2 || true
if [[ -n "$ANTERIOR" ]]; then
  echo "↺ Voltando para $ANTERIOR (o banco já migrado fica; backup em $BACKUP)" >&2
  ln -sfn "$ANTERIOR" "$DESTINO/atual"
  systemctl --user restart "$SERVICO"
fi
exit 1
