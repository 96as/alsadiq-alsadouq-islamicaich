#!/bin/sh
set -e

npm install

# Workaround: npm bug #4828 skips platform-specific optional deps for @tailwindcss/oxide
ARCH=$(uname -m)
if [ "$ARCH" = "aarch64" ]; then PLAT="linux-arm64-gnu";
elif [ "$ARCH" = "x86_64" ]; then PLAT="linux-x64-gnu";
else PLAT=""; fi

if [ -n "$PLAT" ]; then
  npm ls "@tailwindcss/oxide-${PLAT}" >/dev/null 2>&1 || npm install --no-save "@tailwindcss/oxide-${PLAT}"
fi

exec npm run dev -- --host 0.0.0.0
