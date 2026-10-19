"""Aggregate the BEFORE and AFTER eval reports. Reads out/<side>/report-llm-*.json and the full dry reports.
Usage: PYTHONUTF8=1 python analyze.py [--json out/summary.json]
Prints markdown tables. Never prints replies (only ids, counts, tags)."""
import glob, json, math, os, random, statistics, sys
from collections import Counter, defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, 'out')


SPLIT = json.load(open(os.path.join(HERE, '..', 'product-web', 'backend', 'conversation', 'eval', 'split.json'), encoding='utf8'))
HELD, DEV = set(SPLIT['heldout']), set(SPLIT['dev'])


def load_live(side):
    """{'heldout': results, 'dev': results, ...} plus configs. Several reports per split (reruns) merge by case id; the last wins."""
    res, cfg, files = {}, {}, {}
    for f in sorted(glob.glob(os.path.join(OUT, side, 'report-llm-*.json'))):
        d = json.load(open(f, encoding='utf8'))
        split = d['config'].get('filters', {}).get('split') or ('heldout' if 'heldout' in os.path.basename(f) else None)
        files.setdefault(side, []).append(f)
        yield f, d


def rubric_only(r):
    if r['status'] != 'fail' or r.get('policy_failures'):
        return False
    counted = [x for x in (r.get('findings') or []) if x.get('counts', True)]
    return bool(counted) and all(x['tag'] == 'rubric' for x in counted)


def wilson(k, n, z=1.96):
    if not n:
        return (None, None)
    p = k / n
    den = 1 + z * z / n
    c = (p + z * z / (2 * n)) / den
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / den
    return (max(0, c - h), min(1, c + h))


def pct(x):
    return 'n/a' if x is None else f'{round(100 * x)}%'


def rate_cell(k, n):
    if not n:
        return 'n/a'
    lo, hi = wilson(k, n)
    return f'{k}/{n} = {pct(k / n)} ({pct(lo)} to {pct(hi)})'


def mcnemar_exact(b, c):
    n = b + c
    if n == 0:
        return 1.0
    k = min(b, c)
    p = sum(math.comb(n, i) for i in range(0, k + 1)) / 2 ** n
    return min(1.0, 2 * p)


def paired_boot(pairs, iters=10000, seed=7):
    """pairs: list of (before_pass, after_pass) 0/1. Returns 95% bootstrap CI of mean(after) - mean(before)."""
    rng = random.Random(seed)
    n = len(pairs)
    ds = []
    for _ in range(iters):
        s = [pairs[rng.randrange(n)] for _ in range(n)]
        ds.append(sum(a for _b, a in s) / n - sum(b for b, _a in s) / n)
    ds.sort()
    return ds[int(0.025 * iters)], ds[int(0.975 * iters)]


def merge(reports):
    """case-lang-channel key -> result dict; later reports (reruns) replace earlier ones unless the later one is an error."""
    out = {}
    for _f, d in reports:
        for r in d['results']:
            key = (r['case_id'], r['lang'], r['channel'])
            if r['status'] == 'error' and key in out and out[key]['status'] != 'error':
                continue
            out[key] = r
    return out


def tally(rs):
    c = Counter(r['status'] for r in rs)
    pas, fail, gap, err = c['pass'], c['fail'], c['gap'], c['error']
    ro = sum(1 for r in rs if rubric_only(r))
    return dict(pass_=pas, fail=fail, gap=gap, error=err, scored=pas + fail, rubric_only=ro, gates=pas + ro)


def lat(rs):
    xs = sorted(r['latency_s'] for r in rs if r.get('latency_s') and r['status'] in ('pass', 'fail', 'gap'))
    if not xs:
        return None
    p90 = xs[min(len(xs) - 1, int(math.ceil(0.9 * len(xs))) - 1)]
    return dict(n=len(xs), median=statistics.median(xs), mean=statistics.mean(xs), p90=p90, max=xs[-1])


def calls(rs):
    return sum(r.get('agent_calls', 0) for r in rs), sum(r.get('judge_calls', 0) for r in rs)


def main():
    sides = {}
    for side in ('before', 'after'):
        reps = list(load_live(side))
        by_split = defaultdict(list)
        for f, d in reps:
            ids = {r['case_id'] for r in d['results']}
            sp = 'heldout' if ids <= HELD else ('dev' if ids <= DEV else 'mixed')
            by_split[sp].append((f, d))
        sides[side] = {sp: (merge(v), v) for sp, v in by_split.items()}
    summary = {}
    print('# Files')
    for side in sides:
        for sp, (_m, v) in sides[side].items():
            for f, d in v:
                c = d['config']
                a = sum(r.get('agent_calls', 0) for r in d['results'])
                j = sum(r.get('judge_calls', 0) for r in d['results'])
                print(f"- {side} {sp}: {os.path.basename(f)} commit={c.get('commit')} runs={len(d['results'])} agent={a} judge={j} "
                      f"model={c.get('agent_model_resolved')} judge={c.get('judge_model_used')} effort={c.get('reasoning_effort')!r} fp={c.get('fingerprints')}")
    total_calls = 0
    for side in sides:
        for sp, (_m, v) in sides[side].items():
            for _f, d in v:
                total_calls += sum(r.get('agent_calls', 0) + r.get('judge_calls', 0) for r in d['results'])
    print(f'\nTOTAL counted calls over all live reports: {total_calls}')

    cats = sorted({r['category'] for s in sides.values() for sp, (m, _v) in s.items() for r in m.values()})
    sets = {'heldout': ['heldout'], 'dev': ['dev'], 'all': ['heldout', 'dev']}
    for label, sps in sets.items():
        mb = {k: r for sp in sps for k, r in sides['before'].get(sp, ({}, None))[0].items()}
        ma = {k: r for sp in sps for k, r in sides['after'].get(sp, ({}, None))[0].items()}
        common = sorted(set(mb) & set(ma))
        print(f'\n## {label}: runs before {len(mb)}, after {len(ma)}, in both {len(common)}')
        # per category, over the common runs
        print('| Category | Runs | B pass/fail/gap/err | B strict | B gates | A pass/fail/gap/err | A strict | A gates |')
        print('|---|---|---|---|---|---|---|---|')
        for cat in cats + ['ALL']:
            keys = [k for k in common if cat == 'ALL' or mb[k]['category'] == cat]
            if not keys:
                continue
            tb, ta = tally([mb[k] for k in keys]), tally([ma[k] for k in keys])
            def cell(t):
                if not t['scored']:
                    return 'n/a', 'n/a'
                return pct(t['pass_'] / t['scored']), pct(t['gates'] / t['scored'])
            sb, gb = cell(tb)
            sa, ga = cell(ta)
            print(f"| {cat} | {len(keys)} | {tb['pass_']}/{tb['fail']}/{tb['gap']}/{tb['error']} | {sb} | {gb} | "
                  f"{ta['pass_']}/{ta['fail']}/{ta['gap']}/{ta['error']} | {sa} | {ga} |")
        keys = common
        tb, ta = tally([mb[k] for k in keys]), tally([ma[k] for k in keys])
        print(f"\nBEFORE strict {rate_cell(tb['pass_'], tb['scored'])}; gates {rate_cell(tb['gates'], tb['scored'])}")
        print(f"AFTER  strict {rate_cell(ta['pass_'], ta['scored'])}; gates {rate_cell(ta['gates'], ta['scored'])}")
        # paired, over runs scored on both
        both = [k for k in keys if mb[k]['status'] in ('pass', 'fail') and ma[k]['status'] in ('pass', 'fail')]
        fixed = [k for k in both if mb[k]['status'] == 'fail' and ma[k]['status'] == 'pass']
        regr = [k for k in both if mb[k]['status'] == 'pass' and ma[k]['status'] == 'fail']
        pairs = [(1 if mb[k]['status'] == 'pass' else 0, 1 if ma[k]['status'] == 'pass' else 0) for k in both]
        if pairs:
            lo, hi = paired_boot(pairs)
            d = sum(a for _b, a in pairs) / len(pairs) - sum(b for b, _a in pairs) / len(pairs)
            print(f"Paired on {len(both)} runs scored in both: fixed {len(fixed)}, regressed {len(regr)}, exact McNemar p={mcnemar_exact(len(fixed), len(regr)):.4f}, "
                  f"strict change {100 * d:+.1f} points (bootstrap 95% {100 * lo:+.1f} to {100 * hi:+.1f})")
            gp = [(1 if (mb[k]['status'] == 'pass' or rubric_only(mb[k])) else 0, 1 if (ma[k]['status'] == 'pass' or rubric_only(ma[k])) else 0) for k in both]
            gd = sum(a for _b, a in gp) / len(gp) - sum(b for b, _a in gp) / len(gp)
            glo, ghi = paired_boot(gp)
            print(f"Gates change {100 * gd:+.1f} points (bootstrap 95% {100 * glo:+.1f} to {100 * ghi:+.1f})")
            print('fixed ids: ' + ', '.join(f'{k[0]}' for k in fixed))
            print('regressed ids: ' + ', '.join(f'{k[0]}' for k in regr))
        lb, la = lat([mb[k] for k in keys]), lat([ma[k] for k in keys])
        print('latency (agent, seconds inside API calls): before', lb, 'after', la)
        cb, ca = calls([mb[k] for k in keys]), calls([ma[k] for k in keys])
        print('calls agent/judge: before', cb, 'after', ca)
        pt_b = statistics.mean([r['prompt_tokens'] for r in mb.values() if r.get('prompt_tokens')]) if mb else 0
        pt_a = statistics.mean([r['prompt_tokens'] for r in ma.values() if r.get('prompt_tokens')]) if ma else 0
        ct_b = statistics.mean([r['completion_tokens'] for r in mb.values() if r.get('completion_tokens')]) if mb else 0
        ct_a = statistics.mean([r['completion_tokens'] for r in ma.values() if r.get('completion_tokens')]) if ma else 0
        print(f'mean prompt tokens before {pt_b:.0f} after {pt_a:.0f}; mean completion tokens before {ct_b:.0f} after {ct_a:.0f}')
        # hard-check tags
        for nm, m in (('before', mb), ('after', ma)):
            tags = Counter()
            for k in keys:
                r = m[k]
                if r['status'] == 'fail':
                    for f in r.get('findings') or []:
                        if f.get('counts', True):
                            tags[f['tag']] += 1
                    for pf in r.get('policy_failures') or []:
                        tags['policy:' + str(pf['check'])] += 1
            print(nm, 'failed checks:', dict(tags.most_common()))
            print(nm, 'raw guard violations:', sum(1 for k in keys if m[k].get('raw_violations')), 'guard changed:', sum(1 for k in keys if m[k].get('guard_changed')),
                  'errors:', [k[0] for k in keys if m[k]['status'] == 'error'])
        summary[label] = dict(before=tb, after=ta, n_common=len(keys), paired=len(both), fixed=fixed and [k[0] for k in fixed], regressed=[k[0] for k in regr])
    json.dump(summary, open(os.path.join(OUT, 'summary.json'), 'w'), ensure_ascii=False, indent=1)


if __name__ == '__main__':
    main()
