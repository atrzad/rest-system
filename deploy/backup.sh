#!/usr/bin/env bash
# Backup do banco de produção do Rest System (o mesmo formato do backup feito pelo publicar.sh).
# Rodado todo dia pelo rest-system-backup.timer; para rodar agora:
#   systemctl --user start rest-system-backup
# Os arquivos ficam em ~/.local/share/rest-system/backups (os 15 mais novos, contando os do publicar.sh).
# Restaurar: gunzip -c ARQUIVO | docker exec -i rest-system-postgres-1 psql -U USUARIO BANCO
set -euo pipefail

DESTINO="${DESTINO:-$HOME/.local/share/rest-system}"
ENV_PROD="${ENV_PROD:-$HOME/.config/rest-system/producao.env}"
CONTAINER="${CONTAINER:-rest-system-postgres-1}"
MANTER=15

set -a; source "$ENV_PROD"; set +a
BANCO="${DATABASE_URL##*/}"
USUARIO_BANCO="$(sed -E 's#^[^/]*//([^:]+):.*#\1#' <<<"$DATABASE_URL")"

mkdir -p "$DESTINO/backups"
BACKUP="$DESTINO/backups/$BANCO-$(date +%Y%m%d-%H%M%S)-diario.sql.gz"
TEMP="$BACKUP.parcial"
trap 'rm -f "$TEMP"' EXIT

# Grava num arquivo temporário e só renomeia se o pg_dump terminou bem (pipefail),
# para nunca deixar um backup pela metade com cara de bom.
umask 077
docker exec "$CONTAINER" pg_dump -U "$USUARIO_BANCO" "$BANCO" | gzip >"$TEMP"
mv "$TEMP" "$BACKUP"

ls -1t "$DESTINO"/backups/*.sql.gz | tail -n +$((MANTER + 1)) | xargs -r rm --
echo "✓ Backup: $BACKUP ($(du -h "$BACKUP" | cut -f1))"
