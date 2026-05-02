#!/usr/bin/env bash
set -euo pipefail

DB_PATH="${DATABASE_NAME:-/opt/render/project/src/storage/db.sqlite3}"
MEDIA_PATH="${MEDIA_ROOT:-/opt/render/project/src/storage/media}"

mkdir -p "$(dirname "$DB_PATH")" "$MEDIA_PATH"

if [ ! -f "$DB_PATH" ] && [ -f "db.sqlite3" ]; then
    cp db.sqlite3 "$DB_PATH"
fi

if [ -d "media" ] && [ -z "$(find "$MEDIA_PATH" -mindepth 1 -maxdepth 1 -print -quit 2>/dev/null)" ]; then
    cp -a media/. "$MEDIA_PATH"/
fi

python manage.py migrate --noinput
python manage.py provision_superuser
python manage.py seed_demo_data
gunicorn core.wsgi:application --bind 0.0.0.0:"${PORT:-10000}"
