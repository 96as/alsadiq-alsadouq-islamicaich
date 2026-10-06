#!/bin/bash
# usage: drun2.sh <before|after> <extra args to manage.py ...>
# Runs manage.py inside the eval image against one worktree. The .env is mounted as a file at /.env (never printed).
# BEFORE = temporary worktree at origin/hk/01-knowledge-bank (d11da63) plus the eval-only overlay.
# AFTER  = hk/agent-quality after the second sync merge.
SIDE="$1"; shift
if [ "$SIDE" = "before" ]; then WT="$USERPROFILE"'\Documents\Alsadiq-wt\eval-before-d11da63'; else WT="$USERPROFILE"'\Documents\Alsadiq-wt\agent-quality'; fi
COMMIT=$(git -C "$(echo $WT | sed 's#\\#/#g; s#^C:#/c#')" rev-parse --short HEAD)
MSYS_NO_PATHCONV=1 docker run --rm --name "eval2-$SIDE-$$" \
  -v "$WT\\backend:/app" -v "$WT\\.env:/.env:ro" -v "$USERPROFILE"'\Documents\Alsadiq-wt\eval-runs\out2:/out' \
  -e PYTHONUTF8=1 -e "EVAL_COMMIT=$SIDE-$COMMIT" -e LLM_MODEL=gpt-5.4-mini -w /app \
  alsadiq-eval-runner:local python manage.py "$@"
