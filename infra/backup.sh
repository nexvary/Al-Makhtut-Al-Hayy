#!/usr/bin/env sh
set -eu

: "${BACKUP_DIR:?set BACKUP_DIR}"
: "${POSTGRES_CONTAINER:=al-makhtut-postgres}"
: "${OBJECTS_DIR:=/var/lib/al-makhtut/objects}"

stamp="$(date -u +%Y%m%dT%H%M%SZ)"
target="${BACKUP_DIR}/${stamp}"
mkdir -p "${target}"

docker exec "${POSTGRES_CONTAINER}" pg_dump -U makhtut -d makhtut -Fc > "${target}/database.dump"
if [ -d "${OBJECTS_DIR}" ]; then
  tar -C "${OBJECTS_DIR}" -czf "${target}/objects.tar.gz" .
fi

find "${BACKUP_DIR}" -mindepth 1 -maxdepth 1 -type d -mtime +14 -exec rm -rf {} +
echo "backup=${target}"
