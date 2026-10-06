#!/bin/bash
# Run once after first deployment, or when new migrations are added manually.
# NOT run automatically on container start — migrations are triggered via CI/CD deploy.
set -e

# seed_admin needs DJANGO_SUPERUSER_PASSWORD in .env (it refuses the dev default
# when DEBUG is off). Optional: DJANGO_SUPERUSER_USERNAME / DJANGO_SUPERUSER_EMAIL.

echo "Running database migrations..."
docker compose -f docker-compose.prod.yml run --rm backend python manage.py migrate
docker compose -f docker-compose.prod.yml run --rm backend python manage.py migrate --check  # fail loudly if anything is left unapplied

echo "Seeding admin user..."
docker compose -f docker-compose.prod.yml run --rm backend python manage.py seed_admin

echo "Seeding the knowledge bank (idempotent)..."
docker compose -f docker-compose.prod.yml run --rm backend python manage.py seed_content

echo "Seeding the demo families when DEMO_MODE is on (idempotent, never wipes a family in use)..."
docker compose -f docker-compose.prod.yml run --rm backend sh -c 'case "$(printf "%s" "${DEMO_MODE:-}" | tr "[:upper:]" "[:lower:]")" in 1|true|yes|on) python manage.py seed_demo --ensure ;; *) echo "DEMO_MODE is off: demo seed skipped" ;; esac'

# No collectstatic here: static files are baked into the backend image at build time (a run --rm container would throw them away).

echo "Done."
