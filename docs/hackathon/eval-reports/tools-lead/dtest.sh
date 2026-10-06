#!/bin/bash
# usage: dtest.sh <windows worktree path> [manage.py test args ...]
# Runs the Django tests in the eval image against one worktree. No key is mounted.
WT="$1"; shift
MSYS_NO_PATHCONV=1 docker run --rm \
  -v "$WT\\backend:/app" \
  -e PYTHONUTF8=1 -w /app \
  alsadiq-eval-runner:local python manage.py test --settings=config.settings_sqlite_test "$@"
