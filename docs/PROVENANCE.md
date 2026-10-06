# Provenance

This repository is a fresh, single-commit copy of the team's private development repository,
made for the Bathel 2026 Islamic AI Challenge. The organisers approved a separate public repo
whose content is the same as what was built.

| | |
|---|---|
| Private source ref | `origin/hackathon` |
| Private source commit | `9a70a4f5d1cd2fc67eddb6b68be7d39b2b2af168` |
| Exported | 2026-10-06T20:44Z |
| Export script | `scripts/export_public.sh` (kept in the private repo) |

The private history is not carried over, because it holds old credentials that are being
rotated. Left out of this copy:

- `mobile/`: the Expo app, a development build only; the web app is the submission.
- `docs/hackathon/eval-reports/quality-gate-sets/`: the sealed evaluation sets. Publishing them
  would stop them measuring generalisation. Their results are in
  `docs/hackathon/eval-reports/quality-gate-summary.md`.
- Internal team tooling: the team brain MCP config, local Claude settings, the internal
  setup guide, the public-repo scrub checklist, the export script and the internal security
  audit report (its fixes are in the code; it names commits of the private history).
- Every `.env*` file except `.env.example` `.env.production.example` (placeholders and local-dev defaults only).
