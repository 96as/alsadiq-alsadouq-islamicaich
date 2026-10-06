# Eval runner (task 09). Run from the repo root. No API key needed for eval-dry.
# PYTHONUTF8 keeps Arabic output readable on Windows.
PYTHON ?= python
EVAL_SETTINGS ?= config.settings_sqlite_test

.PHONY: eval-dry eval eval-test

# Policy-only plus a dry run of the LLM plan: zero API calls.
eval-dry:
	cd backend && PYTHONUTF8=1 $(PYTHON) manage.py run_eval --settings=$(EVAL_SETTINGS) --dry-run

# Live run, capped at 200 LLM calls by default. Needs OPENAI_API_KEY in backend/.env.
eval:
	cd backend && PYTHONUTF8=1 $(PYTHON) manage.py run_eval --settings=$(EVAL_SETTINGS) --llm $(EVAL_ARGS)

eval-test:
	cd backend && PYTHONUTF8=1 $(PYTHON) manage.py test conversation.eval --settings=$(EVAL_SETTINGS)
