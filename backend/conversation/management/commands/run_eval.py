"""Run the eval cases (task 09).

Usage:
    python manage.py run_eval [--policy-only] [--category C] [--id ID ...] [--lang ar|en]
                              [--channel voice|text] [--smoke] [--tag T] [--exclude-tag T] [--split dev|heldout]
                              [--use-db] [--bank-dir DIR] [--no-fail] [--no-report]
    python manage.py run_eval --dry-run [--sample N] [--seed S]
    python manage.py run_eval --report-from report-llm-<stamp>.json   (re-render, no model call)
    python manage.py run_eval --llm [--max-llm-calls 200] [--sample N|auto] [--seed S]
                              [--agent-model M] [--judge-model M] [--reasoning-effort E]
                              [--concurrency 4] [--tpm 120000] [--no-judge] [--report-dir DIR] [--no-json] [--no-html]

Policy-only (default): no network, no LLM. Seeds the content bank into a throwaway test
database (or ``--use-db`` to use the current one), builds the value index, runs
``prepare_turn`` for every case and channel and compares the policy-decidable expectations.
Exit status 1 when any policy check fails (unless ``--no-fail``).

``--dry-run``: everything the LLM run does before its first call (agent turn policy and prompt,
policy checks, tool schemas, judge prompt, sample plan, call estimate), no API key needed. Writes
a JSON and an HTML report labelled DRY RUN.

``--llm``: the agent's text path (same prompt, retrieval and tools as the voice agent, no audio),
deterministic reply checks, and a strict-rubric judge where needed. Needs OPENAI_API_KEY. Capped
at ``--max-llm-calls`` (agent plus judge calls). Writes a JSON and an HTML report.
"""
import os

from django.core.management import call_command
from django.core.management.base import BaseCommand, CommandError

from conversation.eval import load_cases, runner


class Command(BaseCommand):
    help = 'Run the companion eval cases (policy-only by default; --dry-run and --llm for the full runner).'

    def add_arguments(self, parser):
        parser.add_argument('--policy-only', action='store_true', help='default; no network or LLM')
        parser.add_argument('--llm', action='store_true', help='agent text path + checks + judge (needs OPENAI_API_KEY)')
        parser.add_argument('--dry-run', action='store_true', dest='dry_run',
                            help='the LLM run without any call (no key needed); reports what it would do')
        parser.add_argument('--report-from', dest='report_from', metavar='JSON',
                            help='re-render the HTML and console summary of an earlier --llm or --dry-run JSON report (no model call)')
        parser.add_argument('--category')
        parser.add_argument('--id', action='append', dest='ids')
        parser.add_argument('--lang', choices=['ar', 'en'])
        parser.add_argument('--channel', choices=['voice', 'text'])
        parser.add_argument('--smoke', action='store_true', help='one case per category')
        parser.add_argument('--tag', help='only cases carrying this tag (for example heldout)')
        parser.add_argument('--exclude-tag', dest='exclude_tag', help='skip cases carrying this tag')
        parser.add_argument('--split', choices=['dev', 'heldout'],
                            help='only the cases of one side of eval/split.json (never tune on heldout)')
        parser.add_argument('--use-db', action='store_true', help='use the current DB instead of a temp seeded one')
        parser.add_argument('--bank-dir', help='content directory for seed_content')
        parser.add_argument('--no-fail', action='store_true', help='always exit 0')
        parser.add_argument('--no-report', action='store_true')
        # LLM / dry-run options
        parser.add_argument('--max-llm-calls', type=int, default=200, dest='max_llm_calls',
                            help='hard cap on agent + judge calls (default 200)')
        parser.add_argument('--sample', default='auto', help='number of (case, channel) runs, or auto (fits the cap)')
        parser.add_argument('--seed', type=int, default=0, help='sample order seed')
        parser.add_argument('--agent-model', dest='agent_model', help='default: LLM_MODEL from the environment')
        parser.add_argument('--judge-model', dest='judge_model', help='default: newest accepted, never the agent model')
        parser.add_argument('--reasoning-effort', dest='reasoning_effort',
                            help='agent reasoning effort (default: REASONING_EFFORT env, else provider default)')
        parser.add_argument('--concurrency', type=int, default=4)
        parser.add_argument('--tpm', type=int, default=120000,
                            help='tokens per minute this run may use (the key is shared; 0 = no pacing)')
        parser.add_argument('--no-judge', action='store_true', dest='no_judge', help='deterministic checks only')
        parser.add_argument('--report-dir', dest='report_dir', help='where the reports go (default: the eval folder)')
        parser.add_argument('--no-json', action='store_true')
        parser.add_argument('--no-html', action='store_true')

    def handle(self, *args, **opts):
        if opts['report_from']:
            return self._rerender(opts)
        llm_mode = opts['llm'] or opts['dry_run']
        # the full runner defaults to text only: the voice channel adds the same cases again at the same cost
        channel = opts['channel'] or ('text' if llm_mode else None)
        cases = runner.filter_cases(
            load_cases(), opts['category'], opts['ids'], opts['lang'], channel, opts['smoke'],
            tag=opts['tag'], exclude_tag=opts['exclude_tag'])
        if opts['split']:
            from conversation.eval.make_split import load_split
            side = set(load_split()[opts['split']])
            cases = [c for c in cases if c['id'] in side]
        if not cases:
            raise CommandError('no cases match the filters')
        if opts['llm'] and opts['dry_run']:
            raise CommandError('use --llm or --dry-run, not both')
        if opts['llm'] and not os.getenv('OPENAI_API_KEY'):
            raise CommandError('--llm needs OPENAI_API_KEY in the environment (agent model and judge). '
                               'Use --dry-run to check the setup without a key.')
        if opts['use_db']:
            return self._finish(opts, cases, self._execute(opts, cases))
        from django.test.utils import setup_databases, teardown_databases
        old = setup_databases(verbosity=0, interactive=False)
        try:
            kw = {'dir': opts['bank_dir']} if opts['bank_dir'] else {}
            call_command('seed_content', verbosity=0, **kw)
            out = self._execute(opts, cases)
        finally:
            teardown_databases(old, verbosity=0)
        return self._finish(opts, cases, out)

    def _rerender(self, opts):
        from conversation.eval import llm_runner, reporting
        run = reporting.load_run(opts['report_from'])
        self.stdout.write(llm_runner.console_summary(run))
        if not opts['no_report']:
            kw = dict(json_=not opts['no_json'], html_=not opts['no_html'])
            if opts['report_dir']:
                kw['directory'] = opts['report_dir']
            for p in reporting.write_reports(run, **kw):
                self.stdout.write(f'report: {p}')

    # ------------------------------------------------------------------ modes

    def _index(self):
        """The value index exactly as the agent entrypoint builds it (``_get_value_index``): the
        servable items plus the types each excerpt links to, which decide what the output guard
        licenses (an excerpt linked to a hadith licenses hadith wording)."""
        from conversation.agent.retrieval import build_value_index
        from conversation.agent.turn_pipeline import annotate_linked_types
        index = build_value_index()
        if not index:
            raise CommandError('the bank is empty; seed it (seed_content) or drop --use-db')
        try:
            annotate_linked_types(index)
        except Exception as exc:  # noqa: BLE001 - same fallback as the entrypoint
            self.stderr.write(f'could not read item links ({exc}); excerpts license only their own citations')
        return index

    def _execute(self, opts, cases):
        index = self._index()
        if not (opts['llm'] or opts['dry_run']):
            return 'policy', runner.run_policy(cases, index)
        from conversation.eval import judge, llm_runner
        agent_model = opts['agent_model'] or os.getenv('LLM_MODEL') or 'gpt-5.4-mini'
        judge_on = not opts['no_judge']
        judge_models = judge.pick_judge_model(agent_model, opts['judge_model'])
        sample = None if str(opts['sample']).lower() == 'auto' else int(opts['sample'])
        filters = {k: opts[k] for k in ('category', 'lang', 'channel', 'tag', 'exclude_tag', 'smoke') if opts.get(k)}
        filters['ids'] = opts['ids'] or None
        filters = {k: v for k, v in filters.items() if v}
        common = dict(agent_model=agent_model, judge_models=judge_models, max_calls=opts['max_llm_calls'],
                      sample=sample, seed=opts['seed'], judge_on=judge_on, reasoning_effort=opts['reasoning_effort'],
                      filters=filters)
        if opts['dry_run']:
            return 'dry', llm_runner.run_dry(cases, index, **common)

        def progress(r, n, total, budget):
            self.stdout.write(f"[{n}/{total}] {r.case_id} {r.channel} {r.status}  (calls {budget.used}/{budget.limit})")
        return 'llm', llm_runner.run_llm(cases, index, concurrency=opts['concurrency'], tpm=opts['tpm'], progress=progress, **common)

    def _finish(self, opts, cases, outcome):
        kind, data = outcome
        if kind == 'policy':
            results = data
            self.stdout.write(runner.console_summary(results))
            if not opts['no_report']:
                self.stdout.write(f"report: {runner.write_report(results)}")
            if any(r.status == 'fail' for r in results) and not opts['no_fail']:
                raise SystemExit(1)
            return
        from conversation.eval import llm_runner, reporting
        run = data
        self.stdout.write(llm_runner.console_summary(run))
        if not opts['no_report']:
            kw = dict(json_=not opts['no_json'], html_=not opts['no_html'])
            if opts['report_dir']:
                kw['directory'] = opts['report_dir']
            for p in reporting.write_reports(run, **kw):
                self.stdout.write(f'report: {p}')
        bad = any(r.status in ('fail', 'error') for r in run.results)
        if bad and not opts['no_fail']:
            raise SystemExit(1)
