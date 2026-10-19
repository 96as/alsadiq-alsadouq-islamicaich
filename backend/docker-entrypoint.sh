#!/bin/sh
# Production backend entrypoint: seed the demo pool in the background, then run gunicorn.
#
# With DEMO_MODE=1 the demo families must exist or POST /api/demo/start answers 503.
# This waits until the CI's `migrate` has finished (migrate --check passes), then runs
# `seed_demo --ensure`: it creates only the missing families and never wipes one that a
# visitor holds, so it is safe on every deploy and on every container restart.
# gunicorn starts at once; it does not wait for the seed. If a visitor arrives first on a
# fresh database, the demo start seeds the pool itself (demo/services.py ensure_pool).
#
# This script never runs migrate itself: CI does that (deploy.yml, scripts/init-prod.sh),
# and two concurrent migrates on a fresh database can collide.
set -e

case "$(printf '%s' "${DEMO_MODE:-}" | tr '[:upper:]' '[:lower:]')" in
  1|true|yes|on)
    (
      tries=0
      until python manage.py migrate --check >/dev/null 2>&1; do
        tries=$((tries + 1))
        if [ "$tries" -ge 150 ]; then
          echo "demo seed: migrations still not applied after about 8 minutes; skipping (run: manage.py seed_demo --ensure)"
          exit 0
        fi
        sleep 3
      done
      python manage.py seed_demo --ensure || echo "demo seed failed (run: manage.py seed_demo --ensure)"
    ) &
    ;;
esac

exec gunicorn config.wsgi:application --bind 0.0.0.0:8000 --workers "${GUNICORN_WORKERS:-3}" --timeout 120
