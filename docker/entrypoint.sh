#!/bin/sh
# Entrypoint APM — attend PostgreSQL, puis migrate / collectstatic selon le rôle.
set -eu

wait_for_tcp() {
  host="$1"
  port="$2"
  name="$3"
  retries="${4:-40}"
  echo "Waiting for ${name} at ${host}:${port}..."
  i=0
  while [ "$i" -lt "$retries" ]; do
    if python -c "import socket; s=socket.create_connection(('${host}', int('${port}')), 2); s.close()" 2>/dev/null; then
      echo "${name} is ready."
      return 0
    fi
    i=$((i + 1))
    sleep 2
  done
  echo "ERROR: ${name} not reachable after ${retries} attempts." >&2
  return 1
}

parse_db_host_port() {
  python - <<'PY'
import os
from urllib.parse import urlparse

url = os.environ.get("DATABASE_URL", "")
if not url:
    raise SystemExit("DATABASE_URL is required")
parsed = urlparse(url)
host = parsed.hostname or "db"
port = parsed.port or 5432
print(f"{host} {port}")
PY
}

if [ "${SKIP_DB_WAIT:-0}" != "1" ]; then
  # Ne pas écraser les arguments originaux ($@), sinon `exec "$@"` exécutera "db <port>"
  db_host="$(parse_db_host_port | awk '{print $1}')"
  db_port="$(parse_db_host_port | awk '{print $2}')"
  wait_for_tcp "$db_host" "$db_port" "PostgreSQL"
fi

if [ "${RUN_MIGRATIONS:-0}" = "1" ]; then
  echo "Applying migrations..."
  python manage.py migrate --noinput
fi

if [ "${RUN_COLLECTSTATIC:-0}" = "1" ]; then
  echo "Collecting static files..."
  python manage.py collectstatic --noinput
fi

exec "$@"
