"""Source-timing eval (hk/13): labelled multi-turn child conversations through the real agent, regex-checked.

Usage (from backend/, with OPENAI_API_KEY in the environment):
    python manage.py run_source_timing --settings=config.settings_sqlite_test
        [--repeats 1] [--concurrency 6] [--out DIR] [--label NAME] [--ids e01-broken-window,a05-grandma-died-levant]
        [--channel voice|text] [--max-calls 2000] [--tpm 200000] [--agent-model M] [--reasoning-effort E] [--file PATH]
        (default out: docs/hackathon/eval-reports/source-timing/<label>-<timestamp>/; a relative --out is under the repo root)

Writes summary.json and report.md (one table plus the failing turns with the replies) and prints the table.
Exit code 0 whatever the numbers: read the table. See conversation/eval/source_timing.py for the checks.
"""
import os
from datetime import datetime
from pathlib import Path

from django.core.management import call_command
from django.core.management.base import BaseCommand, CommandError


class Command(BaseCommand):
    help = 'Run the source-timing conversations through the real agent and print offered / creep / ask / not-found rates.'

    def add_arguments(self, parser):
        parser.add_argument('--repeats', type=int, default=1, help='runs per conversation (default 1)')
        parser.add_argument('--concurrency', type=int, default=6)
        parser.add_argument('--out', help='output directory')
        parser.add_argument('--label', default='run', help='name of this run, for example baseline, after')
        parser.add_argument('--ids', help='conversation id(s) to run, comma-separated (default: all)')
        parser.add_argument('--file', help='conversations YAML (default: source_timing.yaml next to the module)')
        parser.add_argument('--channel', choices=['voice', 'text'], default='voice')
        parser.add_argument('--max-calls', type=int, default=2000, dest='max_calls', help='hard cap on agent calls')
        parser.add_argument('--tpm', type=int, default=200000, help='tokens per minute this run may use (0 = no pacing)')
        parser.add_argument('--agent-model', dest='agent_model', help='default: LLM_MODEL from the environment, else gpt-5.4-mini')
        parser.add_argument('--reasoning-effort', dest='reasoning_effort', help='default: REASONING_EFFORT env')

    def handle(self, *args, **opts):
        from conversation.eval import llm_driver, source_timing
        from conversation.eval.dev_conversations import runner as convs

        if not os.getenv('OPENAI_API_KEY'):
            raise CommandError('run_source_timing needs OPENAI_API_KEY in the environment')
        if opts['repeats'] < 1:
            raise CommandError('--repeats must be at least 1')
        ids = [x.strip() for x in (opts['ids'] or '').split(',') if x.strip()]
        try:
            conversations = source_timing.load_set(opts['file'], ids)
        except (ValueError, OSError) as exc:
            raise CommandError(str(exc))
        if not conversations:
            raise CommandError('no conversations to run')
        agent_model = opts['agent_model'] or os.getenv('LLM_MODEL') or 'gpt-5.4-mini'

        import openai
        client = llm_driver.ThrottledClient(openai.AsyncOpenAI(max_retries=2, timeout=90), opts['tpm'])

        from django.test.utils import setup_databases, teardown_databases
        old = setup_databases(verbosity=0, interactive=False)
        try:
            call_command('seed_content', verbosity=0)
            try:
                index = llm_driver.bank_index()
            except RuntimeError as exc:
                raise CommandError(str(exc))

            def progress(run, budget):
                bad = [r for r in run['records'] if source_timing.failing_reasons(r)]
                state = 'ERROR ' + run['error'] if run['error'] else f"{len(bad)} failing of {len(run['records'])}"
                self.stdout.write(f"{run['conv']}#{run['rep']}: {state}  (calls {budget.used}/{budget.limit})")

            run = source_timing.run_set(
                conversations, index, client=client, agent_model=agent_model, repeats=opts['repeats'],
                concurrency=opts['concurrency'], channel=opts['channel'], effort=opts['reasoning_effort'],
                max_calls=opts['max_calls'], label=opts['label'], file_path=opts['file'], progress=progress)
        finally:
            teardown_databases(old, verbosity=0)

        out = Path(opts['out'] or f"docs/hackathon/eval-reports/source-timing/{opts['label']}-{datetime.now():%Y%m%d-%H%M%S}")
        if not out.is_absolute():
            out = convs.REPO / out      # a relative --out is relative to the repo root, not to backend/
        self.stdout.write(source_timing.console_summary(run))
        for p in source_timing.write_reports(run, out):
            self.stdout.write(f'report: {p}')
