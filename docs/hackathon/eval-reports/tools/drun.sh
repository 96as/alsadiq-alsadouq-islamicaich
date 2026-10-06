#!/bin/bash
# usage: drun.sh <before|after> <extra args to manage.py ...>
# Runs manage.py inside the eval image against one worktree. The .env is mounted as a file at /.env (never printed).
SIDE="$1"; shift
if [ "$SIDE" = "before" ]; then WT="$USERPROFILE"'\Documents\Alsadiq-wt\eval-before'; else WT="$USERPROFILE"'\Documents\Alsadiq-wt\product-web'; fi
COMMIT=$(git -C "$(echo $WT | sed 's#\\#/#g; s#^C:#/c#')" rev-parse --short HEAD)
MSYS_NO_PATHCONV=1 docker run --rm --name "eval-$SIDE-$$" \
  -v "$WT\\backend:/app" -v "$WT\\.env:/.env:ro" -v "$USERPROFILE"'\Documents\Alsadiq-wt\eval-runs\out:/out' \
  -e PYTHONUTF8=1 -e "EVAL_COMMIT=$SIDE-$COMMIT" -e LLM_MODEL=gpt-5.4-mini -w /app \
  alsadiq-eval-runner:local python manage.py "$@"
