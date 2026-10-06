"""Search recall report (task 13): how often does ``search_bank`` find the value a child asked about?

Usage (from backend/, OPENAI_API_KEY in the environment unless every argument is already cached):
    python manage.py search_recall --settings=config.settings_sqlite_test
        [--out DIR] [--model M] [--effort E] [--concurrency 8] [--tpm 400000]
        [--refresh-args] [--no-llm] [--baseline search-recall-before.json] [--notes FILE] [--file PHRASINGS.yaml]

Writes search-recall.md and search-recall.json next to the model-argument cache
(default docs/hackathon/eval-reports/source-timing/). See conversation/eval_support/search_recall.py.
"""
import json
import os
from pathlib import Path

from django.core.management import call_command
from django.core.management.base import BaseCommand, CommandError


class Command(BaseCommand):
    help = 'Run ~380 child phrasings through search_bank (raw and with the real model arguments) and report recall.'

    def add_arguments(self, parser):
        parser.add_argument('--out', help='output directory (also holds the model-argument cache)')
        parser.add_argument('--model', help='default: LLM_MODEL from the environment, else gpt-5.4-mini')
        parser.add_argument('--effort', default='none', help="reasoning effort sent with the call (production: none)")
        parser.add_argument('--concurrency', type=int, default=8)
        parser.add_argument('--tpm', type=int, default=400000)
        parser.add_argument('--refresh-args', action='store_true', dest='refresh', help='ask the model again for every phrasing')
        parser.add_argument('--no-llm', action='store_true', dest='no_llm', help='use the cached model arguments only')
        parser.add_argument('--baseline', help='an earlier search-recall json: its numbers are shown as "before"')
        parser.add_argument('--file', help='phrasings YAML (default: eval/search_recall_phrasings.yaml)')
        parser.add_argument('--notes', help='a markdown file appended to the report (what was fixed, caveats)')

    def handle(self, *args, **opts):
        from conversation.eval import llm_driver
        from conversation.eval_support import search_recall as sr

        out = Path(opts['out']) if opts['out'] else sr.OUT_DIR
        out.mkdir(parents=True, exist_ok=True)
        cache_path = out / 'search-recall-args.json'
        model = opts['model'] or os.getenv('LLM_MODEL') or 'gpt-5.4-mini'
        cases = sr.load_phrasings(Path(opts['file']) if opts['file'] else sr.PHRASINGS_PATH)
        stored = json.loads(cache_path.read_text(encoding='utf-8')) if cache_path.exists() and not opts['refresh'] else {}
        cache = dict(stored.get('args', {}))
        baseline = None
        if opts['baseline']:
            baseline = json.loads(Path(opts['baseline']).read_text(encoding='utf-8')).get('summary')

        from django.test.utils import setup_databases, teardown_databases
        old = setup_databases(verbosity=0, interactive=False)
        try:
            call_command('seed_content', verbosity=0)
            try:
                index = llm_driver.bank_index()
            except RuntimeError as exc:
                raise CommandError(str(exc))
            missing = [c for c in cases if sr.case_key(c) not in cache]
            if missing and not opts['no_llm']:
                if not os.getenv('OPENAI_API_KEY'):
                    raise CommandError('search_recall needs OPENAI_API_KEY in the environment (or --no-llm with a cache)')
                import asyncio
                import openai
                client = llm_driver.ThrottledClient(openai.AsyncOpenAI(max_retries=2, timeout=90), opts['tpm'])
                self.stdout.write(f'asking {model} for the search_bank arguments of {len(missing)} phrasings ...')
                asyncio.run(sr.ask_models(
                    client, model, index, cases, cache, effort=opts['effort'], concurrency=opts['concurrency'],
                    progress=lambda n, total: n % 40 == 0 and self.stdout.write(f'  {n}/{total}')))
                cache_path.write_text(json.dumps({'model': stored.get('model', model), 'effort': opts['effort'], 'args': cache},
                                                 ensure_ascii=False, indent=1, sort_keys=True) + '\n', encoding='utf-8')
            errors = [k for k, v in cache.items() if 'error' in v]
            if errors:
                self.stdout.write(f'{len(errors)} phrasings have no model arguments (API error); run again to retry them')
                cache = {k: v for k, v in cache.items() if 'error' not in v}
                cache_path.write_text(json.dumps({'model': model, 'effort': opts['effort'], 'args': cache},
                                                 ensure_ascii=False, indent=1, sort_keys=True) + '\n', encoding='utf-8')
            rows, summary, misses, md, meta = sr.build_report(
                index, cases, cache, {'model': stored.get('model', model), 'effort': opts['effort']}, baseline)
        finally:
            teardown_databases(old, verbosity=0)

        if opts['notes']:
            md += '\n' + Path(opts['notes']).read_text(encoding='utf-8')
        (out / 'search-recall.md').write_text(md, encoding='utf-8')
        (out / 'search-recall.json').write_text(json.dumps(
            {'meta': meta, 'summary': summary, 'top_misses': misses, 'rows': rows}, ensure_ascii=False, indent=1) + '\n',
            encoding='utf-8')
        for mode in ('a', 'b'):
            s = summary.get(mode)
            if s:
                self.stdout.write(f"({mode}) not found {s['not_found']:.1%}, right value {s['right_value']:.1%}, "
                                  f"misses {s['miss_classes']}")
        self.stdout.write(f'report: {out / "search-recall.md"}')
