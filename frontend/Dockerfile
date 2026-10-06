# Stage 1: Build
FROM node:20-slim AS build
WORKDIR /web

# Copy only package.json (not package-lock.json) so npm resolves all
# platform-specific optional native binaries fresh for the build OS.
# The macOS-generated lockfile skips linux native deps (npm#4828).
COPY package.json ./
RUN npm install

COPY . .

ARG VITE_API_BASE_URL
ENV VITE_API_BASE_URL=${VITE_API_BASE_URL}

# Feature flags, baked in at build time. The app only treats the exact string
# "1" as on; anything else (including empty) leaves the feature off.
ARG VITE_FOREST_SCENE=0
ENV VITE_FOREST_SCENE=${VITE_FOREST_SCENE}
ARG VITE_DEMO_MODE=0
ENV VITE_DEMO_MODE=${VITE_DEMO_MODE}

RUN npm run build

# Stage 2: Export built files for Caddy to serve.
# Caddy reads them from the frontend_dist named volume (docker-compose.prod.yml).
# Docker fills a named volume from the image only once, when it is empty, so a
# plain COPY to /srv/frontend kept serving the first build after every later
# deploy. Instead, keep the build in /dist and copy it into the volume each time
# the container starts (compose recreates it whenever the image changes). Old
# hashed assets stay behind, which is harmless and keeps open tabs working.
FROM busybox:1.36
COPY --from=build /web/dist /dist
CMD ["sh", "-c", "mkdir -p /srv/frontend && cp -a /dist/. /srv/frontend/ && echo 'frontend: new build copied into /srv/frontend'"]
