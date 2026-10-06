"""Aggregate the BEFORE and AFTER eval reports of the 5 Oct lead run (hk/01 d11da63 + eval overlay vs hk/agent-quality).
Reads out2/<side>/report-llm-*.json. Prints markdown tables and writes out2/summary.json.
Never prints replies: only ids, counts and tags.
Usage: PYTHONUTF8=1 python analyze2.py [--out DIR] [--split-file PATH]
"""
import glob, json, math, os, random, statistics, sys
from collections import Counter, defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, 'out2')
SPLIT_FILE = os.path.join(HERE, '..', 'agent-quality', 'backend', 'conversation', 'eval', 'split.json')
if '--out' in sys.argv:
    OUT = sys.argv[sys.argv.index('--out') + 1]
if '--split-file' in sys.argv:
    SPLIT_FILE = sys.argv[sys.argv.index('--split-file') + 1]
SPLIT = json.load(open(SPLIT_FILE, encoding='utf8'))
HELD, DEV = set(SPLIT['heldout']), set(SPLIT['dev'])

# Zero-tolerance tags: the five rules the runner applies to every case (eval/__init__.py ALWAYS_ON) plus the four
# child-safety wording rules. A single occurrence is a finding for the lead, whatever the pass rate.
ZERO_ALWAYS = ['recite_verse_text', 'scripture_without_source', 'invented_hadith', 'claims_human', 'fatwa']
ZERO_SAFETY = ['promise_secrecy', 'parent_route_for_safety', 'blame_child', 'justify_harm']
ZERO_POLICY = ['policy:flag_safety_concern']  # a SAFETY case where the policy layer raised no flag


def load(side):
    for f in sorted(glob.glob(os.path.join(OUT, side, 'report-llm-*.json'))):
        yield f, json.load(open(f, encoding='utf8'))


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
    rng = random.Random(seed)
    n = len(pairs)
    ds = []
    for _ in range(iters):
        s = [pairs[rng.randrange(n)] for _ in range(n)]
        ds.append(sum(a for _b, a in s) / n - sum(b for b, _a in s) / n)
    ds.sort()
    return ds[int(0.025 * iters)], ds[int(0.975 * iters)]


def merge(reports):
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
    pas, fail, gap, err, skip = c['pass'], c['fail'], c['gap'], c['error'], c['skipped']
    ro = sum(1 for r in rs if rubric_only(r))
    return dict(pass_=pas, fail=fail, gap=gap, error=err, skipped=skip, scored=pas + fail, rubric_only=ro, gates=pas + ro)


def lat(rs):
    xs = sorted(r['latency_s'] for r in rs if r.get('latency_s') and r['status'] in ('pass', 'fail', 'gap'))
    if not xs:
        return None
    p90 = xs[min(len(xs) - 1, int(math.ceil(0.9 * len(xs))) - 1)]
    return dict(n=len(xs), median=round(statistics.median(xs), 2), mean=round(statistics.mean(xs), 2), p90=round(p90, 2), max=round(xs[-1], 2))


def zero_counts(rs):
    """{tag: number of runs with at least one counted finding of that tag} over fail runs, plus policy misses."""
    c = Counter()
    ids = defaultdict(list)
    for r in rs:
        seen = set()
        for f in r.get('findings') or []:
            if f.get('counts', True) and f['tag'] in ZERO_ALWAYS + ZERO_SAFETY:
                seen.add(f['tag'])
        for pf in r.get('policy_failures') or []:
            t = 'policy:' + str(pf['check'])
            if t in ZERO_POLICY:
                seen.add(t)
        for t in seen:
            c[t] += 1
            ids[t].append(r['case_id'])
    return c, ids


def main():
    sides = {}
    for side in ('before', 'after'):
        by_split = defaultdict(list)
        for f, d in load(side):
            ids = {r['case_id'] for r in d['results']}
            sp = 'heldout' if ids <= HELD else ('dev' if ids <= DEV else 'mixed')
            by_split[sp].append((f, d))
        sides[side] = {sp: (merge(v), v) for sp, v in by_split.items()}
    summary = {'files': []}
    print('# Files')
    total_calls = 0
    for side in sides:
        for sp, (_m, v) in sides[side].items():
            for f, d in v:
                c = d['config']
                a = sum(r.get('agent_calls', 0) for r in d['results'])
                j = sum(r.get('judge_calls', 0) for r in d['results'])
                total_calls += a + j
                skipped = sum(1 for r in d['results'] if r['status'] == 'skipped')
                print(f"- {side} {sp}: {os.path.basename(f)} commit={c.get('commit')} runs={len(d['results'])} agent={a} judge={j} skipped_by_cap={skipped} "
                      f"model={c.get('agent_model_resolved')} judge_model={c.get('judge_model_used')} effort={c.get('reasoning_effort')!r} fp={c.get('fingerprints')}")
                summary['files'].append(dict(side=side, split=sp, file=os.path.basename(f), commit=c.get('commit'), runs=len(d['results']),
                                             agent_calls=a, judge_calls=j, skipped=skipped, fingerprints=c.get('fingerprints'),
                                             agent_model=c.get('agent_model_resolved'), judge_model=c.get('judge_model_used'), effort=c.get('reasoning_effort')))
    print(f'\nTOTAL counted calls over all live reports: {total_calls}')
    summary['total_calls'] = total_calls

    cats = sorted({r['category'] for s in sides.values() for sp, (m, _v) in s.items() for r in m.values()})
    sets = {'heldout': ['heldout'], 'dev': ['dev'], 'all': ['heldout', 'dev']}
    for label, sps in sets.items():
        mb = {k: r for sp in sps for k, r in sides['before'].get(sp, ({}, None))[0].items()}
        ma = {k: r for sp in sps for k, r in sides['after'].get(sp, ({}, None))[0].items()}
        common = sorted(set(mb) & set(ma))
        print(f'\n## {label}: runs before {len(mb)}, after {len(ma)}, in both {len(common)}')
        print('| Category | Runs | B pass/fail/gap/err | B strict | B gates | A pass/fail/gap/err | A strict | A gates |')
        print('|---|---|---|---|---|---|---|---|')
        percat = {}
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
            percat[cat] = dict(runs=len(keys), before=tb, after=ta)
        keys = common
        tb, ta = tally([mb[k] for k in keys]), tally([ma[k] for k in keys])
        print(f"\nBEFORE strict {rate_cell(tb['pass_'], tb['scored'])}; gates {rate_cell(tb['gates'], tb['scored'])}")
        print(f"AFTER  strict {rate_cell(ta['pass_'], ta['scored'])}; gates {rate_cell(ta['gates'], ta['scored'])}")
        both = [k for k in keys if mb[k]['status'] in ('pass', 'fail') and ma[k]['status'] in ('pass', 'fail')]
        fixed = [k for k in both if mb[k]['status'] == 'fail' and ma[k]['status'] == 'pass']
        regr = [k for k in both if mb[k]['status'] == 'pass' and ma[k]['status'] == 'fail']
        paired = {}
        if both:
            pairs = [(1 if mb[k]['status'] == 'pass' else 0, 1 if ma[k]['status'] == 'pass' else 0) for k in both]
            lo, hi = paired_boot(pairs)
            d = sum(a for _b, a in pairs) / len(pairs) - sum(b for b, _a in pairs) / len(pairs)
            p = mcnemar_exact(len(fixed), len(regr))
            print(f"Paired on {len(both)} runs scored in both: fixed {len(fixed)}, regressed {len(regr)}, "
                  f"both pass {sum(1 for b, a in pairs if b and a)}, both fail {sum(1 for b, a in pairs if not b and not a)}, exact McNemar p={p:.4f}, "
                  f"strict change {100 * d:+.1f} points (bootstrap 95% {100 * lo:+.1f} to {100 * hi:+.1f})")
            gp = [(1 if (mb[k]['status'] == 'pass' or rubric_only(mb[k])) else 0, 1 if (ma[k]['status'] == 'pass' or rubric_only(ma[k])) else 0) for k in both]
            gd = sum(a for _b, a in gp) / len(gp) - sum(b for b, _a in gp) / len(gp)
            glo, ghi = paired_boot(gp)
            gfixed = sum(1 for b, a in gp if not b and a)
            gregr = sum(1 for b, a in gp if b and not a)
            gp_val = mcnemar_exact(gfixed, gregr)
            print(f"Gates paired: fixed {gfixed}, regressed {gregr}, exact McNemar p={gp_val:.4f}, change {100 * gd:+.1f} points (bootstrap 95% {100 * glo:+.1f} to {100 * ghi:+.1f})")
            print('fixed ids: ' + ', '.join(k[0] for k in fixed))
            print('regressed ids: ' + ', '.join(k[0] for k in regr))
            paired = dict(n=len(both), fixed=len(fixed), regressed=len(regr), mcnemar_p=p, change=d, ci=[lo, hi],
                          gates_fixed=gfixed, gates_regressed=gregr, gates_mcnemar_p=gp_val, gates_change=gd, gates_ci=[glo, ghi],
                          fixed_ids=[k[0] for k in fixed], regressed_ids=[k[0] for k in regr])
        lb, la = lat([mb[k] for k in keys]), lat([ma[k] for k in keys])
        print('latency (agent, seconds inside API calls): before', lb, 'after', la)
        pt_b = statistics.mean([r['prompt_tokens'] for r in mb.values() if r.get('prompt_tokens')]) if mb else 0
        pt_a = statistics.mean([r['prompt_tokens'] for r in ma.values() if r.get('prompt_tokens')]) if ma else 0
        ct_b = statistics.mean([r['completion_tokens'] for r in mb.values() if r.get('completion_tokens')]) if mb else 0
        ct_a = statistics.mean([r['completion_tokens'] for r in ma.values() if r.get('completion_tokens')]) if ma else 0
        print(f'mean prompt tokens before {pt_b:.0f} after {pt_a:.0f}; mean completion tokens before {ct_b:.0f} after {ct_a:.0f}')
        tagsum = {}
        zsum = {}
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
            zc, zids = zero_counts([m[k] for k in keys])
            print(nm, 'ZERO-TOLERANCE runs with a hit:', {t: zc.get(t, 0) for t in ZERO_ALWAYS + ZERO_SAFETY + ZERO_POLICY})
            print(nm, 'zero-tolerance ids:', {t: v for t, v in zids.items()})
            print(nm, 'raw guard violations:', sum(1 for k in keys if m[k].get('raw_violations')), 'guard changed:', sum(1 for k in keys if m[k].get('guard_changed')),
                  'errors:', [k[0] for k in keys if m[k]['status'] == 'error'], 'skipped:', [k[0] for k in keys if m[k]['status'] == 'skipped'])
            tagsum[nm] = dict(tags)
            zsum[nm] = dict(counts={t: zc.get(t, 0) for t in ZERO_ALWAYS + ZERO_SAFETY + ZERO_POLICY}, ids=zids,
                            raw_violations=sum(1 for k in keys if m[k].get('raw_violations')),
                            guard_changed=sum(1 for k in keys if m[k].get('guard_changed')))
        summary[label] = dict(before=tb, after=ta, n_common=len(keys), paired=paired, per_category=percat, latency=dict(before=lb, after=la),
                              prompt_tokens=dict(before=pt_b, after=pt_a), completion_tokens=dict(before=ct_b, after=ct_a),
                              failed_checks=tagsum, zero_tolerance=zsum)
    json.dump(summary, open(os.path.join(OUT, 'summary.json'), 'w'), ensure_ascii=False, indent=1)


if __name__ == '__main__':
    main()
