"""Hybrid companion probes (hk/12): about 50 labelled child messages through the real agent, regex-checked.

Usage (from backend/, with OPENAI_API_KEY in the environment):
    python manage.py run_hybrid_probes --settings=config.settings_sqlite_test
        [--repeats 2] [--only religious,grooming] [--concurrency 6] [--out DIR] [--label NAME]
        [--channel voice|text] [--max-calls 800] [--tpm 200000] [--agent-model M] [--reasoning-effort E] [--file PATH]
        (default out: docs/hackathon/eval-reports/hybrid/probes-<label>-<timestamp>/ at the repo root)

Writes summary.json and report.md (one table plus the failing transcripts) and prints the table. Exit code 0
whether probes pass or not: read the table. See conversation/eval/hybrid_probes.py for the checks.
"""
import os
from datetime import datetime
from pathlib import Path

from django.core.management import call_command
from django.core.management.base import BaseCommand, CommandError


class Command(BaseCommand):
    help = 'Run the labelled hybrid-companion probes through the real agent and print pass rates per label.'

    def add_arguments(self, parser):
        parser.add_argument('--repeats', type=int, default=2, help='runs per probe (default 2)')
        parser.add_argument('--only', help='label(s) to run, comma-separated (default: all)')
        parser.add_argument('--concurrency', type=int, default=6)
        parser.add_argument('--out', help='output directory')
        parser.add_argument('--label', default='run', help='name of this run, for example smoke, hybrid')
        parser.add_argument('--file', help='probes YAML (default: hybrid_probes.yaml next to the module)')
        parser.add_argument('--channel', choices=['voice', 'text'], default='voice')
        parser.add_argument('--max-calls', type=int, default=800, dest='max_calls', help='hard cap on agent calls')
        parser.add_argument('--tpm', type=int, default=200000, help='tokens per minute this run may use (0 = no pacing)')
        parser.add_argument('--agent-model', dest='agent_model', help='default: LLM_MODEL from the environment, else gpt-5.4-mini')
        parser.add_argument('--reasoning-effort', dest='reasoning_effort', help='default: REASONING_EFFORT env')

    def handle(self, *args, **opts):
        from conversation.eval import hybrid_probes, llm_driver
        from conversation.eval.dev_conversations import runner as convs

        if not os.getenv('OPENAI_API_KEY'):
            raise CommandError('run_hybrid_probes needs OPENAI_API_KEY in the environment')
        if opts['repeats'] < 1:
            raise CommandError('--repeats must be at least 1')
        try:
            probes = hybrid_probes.load_probes(opts['file'], opts['only'])
        except (ValueError, OSError) as exc:
            raise CommandError(str(exc))
        if not probes:
            raise CommandError('no probes to run')
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

            def progress(rec, budget):
                verdict = 'ERROR' if rec['pass'] is None else 'pass' if rec['pass'] else 'FAIL ' + ','.join(rec['failed'])
                self.stdout.write(f"{rec['id']}#{rec['rep']}: {verdict}  (calls {budget.used}/{budget.limit})")

            run = hybrid_probes.run_probes(
                probes, index, client=client, agent_model=agent_model, repeats=opts['repeats'],
                concurrency=opts['concurrency'], channel=opts['channel'], effort=opts['reasoning_effort'],
                max_calls=opts['max_calls'], label=opts['label'], file_path=opts['file'], progress=progress)
        finally:
            teardown_databases(old, verbosity=0)

        out = Path(opts['out']) if opts['out'] else (
            convs.REPO / 'docs/hackathon/eval-reports/hybrid' / f"probes-{opts['label']}-{datetime.now():%Y%m%d-%H%M%S}")
        self.stdout.write(hybrid_probes.console_summary(run))
        for p in hybrid_probes.write_reports(run, out):
            self.stdout.write(f'report: {p}')
