#!/bin/bash
# Four live runs, one after the other (the org token limit is shared). Hard caps sum to 670 counted calls (limit 700).
# usage: run_all.sh   (started in the background; logs go to out/<side>/console-<split>.log)
cd "$HOME"/Documents/Alsadiq-wt/eval-runs
COMMON="--settings=config.settings_sqlite_test --llm --channel text --reasoning-effort none --tpm 100000 --concurrency 4"
for side in before after; do
  mkdir -p out/$side
  bash drun.sh $side run_eval $COMMON --split heldout --sample 50 --seed 0 --max-llm-calls 110 --report-dir /out/$side > out/$side/console-heldout.log 2>&1
  echo "$side heldout done rc=$?" >> out/progress.log
  bash drun.sh $side run_eval $COMMON --split dev --sample 110 --seed 1 --max-llm-calls 225 --report-dir /out/$side > out/$side/console-dev.log 2>&1
  echo "$side dev done rc=$?" >> out/progress.log
done
echo ALL DONE >> out/progress.log
