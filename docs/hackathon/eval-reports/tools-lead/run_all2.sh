#!/bin/bash
# Four live runs, one after the other (the org token limit is shared).
# Hard caps sum to 400 counted calls: 2 x 108 (held-out) + 2 x 92 (dev sample).
# BEFORE = origin/hk/01-knowledge-bank d11da63 + eval-only overlay; AFTER = hk/agent-quality after the second sync merge.
# usage: run_all2.sh   (started in the background; logs go to out2/<side>/console-<split>.log)
cd "$HOME"/Documents/Alsadiq-wt/eval-runs
COMMON="--settings=config.settings_sqlite_test --llm --channel text --reasoning-effort none --tpm 100000 --concurrency 3"
for side in before after; do
  mkdir -p out2/$side
  bash drun2.sh $side run_eval $COMMON --split heldout --sample 50 --seed 0 --max-llm-calls 108 --report-dir /out/$side > out2/$side/console-heldout.log 2>&1
  echo "$side heldout done rc=$?" >> out2/progress.log
done
for side in before after; do
  bash drun2.sh $side run_eval $COMMON --split dev --sample 40 --seed 1 --max-llm-calls 92 --report-dir /out/$side > out2/$side/console-dev.log 2>&1
  echo "$side dev done rc=$?" >> out2/progress.log
done
echo ALL DONE >> out2/progress.log
