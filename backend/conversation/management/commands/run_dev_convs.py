"""Multi-turn dev conversation eval for prompt variants (hk/11).

Usage (from backend/, with OPENAI_API_KEY in the environment):
    python manage.py run_dev_convs --label baseline --settings=config.settings_sqlite_test
        [--ids a,b] [--file PATH] [--channel voice|text] [--no-judge] [--max-calls 600]
        [--concurrency 6] [--tpm 200000] [--agent-model M] [--judge-model M] [--reasoning-effort E]
        [--out DIR]    (default: docs/hackathon/eval-reports/dev-convs/<label>-<timestamp>/ at the repo root)

Runs the scripted child conversations through the real agent (prompt, turn guard, the live search_bank
tool), then scores each whole conversation with an LLM judge. Run the same command in each variant's worktree.
"""
import os
from datetime import datetime
from pathlib import Path

from django.core.management import call_command
from django.core.management.base import BaseCommand, CommandError

from conversation.eval import llm_driver


class Command(BaseCommand):
    help = 'Run scripted multi-turn child conversations through the real agent and judge each whole conversation.'

    def add_arguments(self, parser):
        parser.add_argument('--label', default='run', help='variant name, for example baseline, A, B')
        parser.add_argument('--ids', help='comma-separated conversation ids (default: all)')
        parser.add_argument('--file', help='conversations YAML (default: conversations.yaml next to the runner)')
        parser.add_argument('--channel', choices=['voice', 'text'], default='voice')
        parser.add_argument('--out', help='output directory')
        parser.add_argument('--no-judge', action='store_true', dest='no_judge')
        parser.add_argument('--max-calls', type=int, default=600, dest='max_calls', help='hard cap on agent + judge calls')
        parser.add_argument('--concurrency', type=int, default=6)
        parser.add_argument('--tpm', type=int, default=200000, help='tokens per minute this run may use (0 = no pacing)')
        parser.add_argument('--agent-model', dest='agent_model', help='default: LLM_MODEL from the environment, else gpt-5.4-mini')
        parser.add_argument('--judge-model', dest='judge_model', help='default: newest accepted, never the agent model')
        parser.add_argument('--reasoning-effort', dest='reasoning_effort', help='default: REASONING_EFFORT env')

    def handle(self, *args, **opts):
        from conversation.eval import judge
        from conversation.eval.dev_conversations import runner

        if not os.getenv('OPENAI_API_KEY'):
            raise CommandError('run_dev_convs needs OPENAI_API_KEY in the environment (agent and judge)')
        ids = [i.strip() for i in opts['ids'].split(',') if i.strip()] if opts['ids'] else None
        try:
            convs = runner.load_conversations(opts['file'], ids)
        except (ValueError, OSError) as exc:
            raise CommandError(str(exc))
        if not convs:
            raise CommandError('no conversations to run')
        agent_model = opts['agent_model'] or os.getenv('LLM_MODEL') or 'gpt-5.4-mini'
        judge_models = judge.pick_judge_model(agent_model, opts['judge_model'])

        import openai
        client = llm_driver.ThrottledClient(openai.AsyncOpenAI(max_retries=2, timeout=90), opts['tpm'])

        from django.test.utils import setup_databases, teardown_databases
        old = setup_databases(verbosity=0, interactive=False)
        try:
            call_command('seed_content', verbosity=0)
            index = self._index()

            def progress(res, budget):
                self.stdout.write(f"{res['id']}: {len(res['turns'])} turns{'  ERROR ' + res['error'] if res['error'] else ''}"
                                  f"  (calls {budget.used}/{budget.limit})")
            run = runner.run_dev_convs(
                convs, index, client=client, agent_model=agent_model, judge_models=judge_models, label=opts['label'],
                channel=opts['channel'], effort=opts['reasoning_effort'], max_calls=opts['max_calls'],
                concurrency=opts['concurrency'], judge_on=not opts['no_judge'], file_path=opts['file'], progress=progress)
        finally:
            teardown_databases(old, verbosity=0)

        out = Path(opts['out']) if opts['out'] else (
            runner.REPO / 'docs/hackathon/eval-reports/dev-convs' / f"{opts['label']}-{datetime.now():%Y%m%d-%H%M%S}")
        self.stdout.write(runner.console_summary(run))
        for p in runner.write_reports(run, out):
            self.stdout.write(f'report: {p}')

    def _index(self):
        """The value index as the agent entrypoint builds it (same as run_eval)."""
        try:
            return llm_driver.bank_index()
        except RuntimeError as exc:
            raise CommandError(str(exc))
