FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential libpq-dev \
  && rm -rf /var/lib/apt/lists/*

COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

COPY . /app

# Static files (admin CSS, /static/quran/ mp3s) are baked into the image and served by WhiteNoise.
# Build-only dummy secrets (settings refuse an empty or dev LiveKit secret when DEBUG=0); a failure must break the build, so there is no `|| true`.
RUN DJANGO_SECRET_KEY=collectstatic-build-only LIVEKIT_API_SECRET=collectstatic-build-only-not-a-real-secret DEBUG=0 python manage.py collectstatic --noinput

EXPOSE 8000

# Runs gunicorn (3 workers, GUNICORN_WORKERS to change) and, with DEMO_MODE=1, seeds the
# demo family pool in the background once migrations are applied. See docker-entrypoint.sh.
# `sh` is explicit so the file needs no executable bit.
CMD ["sh", "/app/docker-entrypoint.sh"]
