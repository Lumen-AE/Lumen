"""Recount full-plan RTL traces through two different Python sampling paths."""
import argparse
from collections import Counter
from functools import lru_cache
import hashlib
import json
from pathlib import Path
import sys

from lumen.paths import ROOT
from lumen.coverage.definitions import CoverageModel
from lumen.coverage.scorer import FullCoverage, model
from lumen.observation.probes import transactions
from lumen.observation.samples import FSM
from lumen.engine import artifacts


REFERENCE_CACHE = {}


@lru_cache(maxsize=3)
def transition_keys(group):
    return tuple(key for key, r in model()[0].items() if r['group'] == group
                 and r['kind'] != 'cross' and any('transition' in b for b in r['bins']))


def reference_sample(reference, group, instance, values, gates, cached=True):
    """Memoize the unchanged source-model sampler, including transition state.

    This changes only recount speed. Every cache entry is computed by the
    original CoverageModel.sample, independently of the indexed RTL scorer.
    """
    if not cached:
        return reference.sample(group, values, gates, instance=instance)
    suffix = '@' + str(instance) if group == 'pmp_region_cg' else ''
    history = tuple((key + suffix, reference.previous.get(key + suffix)) for key in transition_keys(group))
    key = (group, instance, tuple(sorted(values.items())), tuple(sorted(gates.items())), history)
    if key not in REFERENCE_CACHE:
        single = CoverageModel.__new__(CoverageModel)
        single.defs, single.targets = reference.defs, reference.targets
        single.hits = Counter()
        single.previous = dict(history)
        single.observed = set()
        single.missing_inputs = Counter()
        single.sample(group, values, gates, instance=instance)
        assert not single.missing_inputs, single.missing_inputs
        REFERENCE_CACHE[key] = (single.hits, single.previous, single.observed)
    hits, previous, observed = REFERENCE_CACHE[key]
    reference.hits.update(hits)
    reference.previous.update(previous)
    reference.observed.update(observed)


def audit(folder, cached=True):
    report = artifacts.read_json(folder / 'report.json')
    fast = FullCoverage(report['catalog'])
    # Historical full-plan reports retain the original 4450-key count vector.
    # Freeze never rewrites those records or silently scores a smaller vector.
    if set(fast.hits) != set(report['primary']['counts']):
        # Reconstruct the captured vector from the current 4814-bin partition.
        # This audits old bytes without keeping an obsolete scoring catalog.
        records = dict(fast.records)
        records.update((r['target']['id'], r['target']) for r in
                       artifacts.read_json(ROOT / 'targets/ibex/coverage/excluded.json'))
        saved = report['primary']['counts']
        assert set(saved) <= set(records), 'unknown official bin in saved report'
        fast.records = {key: records[key] for key in saved}
        fast.hits = Counter({key: 0 for key in saved})
    reference = CoverageModel.__new__(CoverageModel)
    reference.defs, reference.targets = model()
    reference.hits = Counter()
    reference.previous = {}
    reference.observed = set()
    reference.missing_inputs = Counter()
    rows = 0
    profiles_seen = set()
    with artifacts.open_text(folder / 'internal_trace.jsonl') as stream:
        return audit_rows(folder, report, fast, reference, stream, cached)


def audit_rows(folder, report, fast, reference, stream, cached):
    rows = 0
    profiles_seen = set()
    for line in stream:
        row = json.loads(line)
        if row['reset_n'] and row['core_edge']:
            profiles_seen.add(row['profile'])
        rows += 1
        actual_new = fast.sample(row, row['cycle'])
        assert sorted(actual_new) == sorted(row['new_bins']), ('new_bins', folder, row['cycle'])
        if not row['reset_n']:
            reference.reset()
        elif row['core_edge']:
            for (group, instance), tx in transactions(row['official_bus']).items():
                if group != 'uarch_cg' and not row['profile'] & 2:
                    continue
                values = dict(tx['values'])
                for key in ('cp_controller_fsm', 'cp_controller_fsm_sleep'):
                    if key in values:
                        values[key] = FSM[values[key]]
                reference_sample(reference, group, instance or 0, values, tx['gates'], cached=cached)
    assert not reference.missing_inputs, reference.missing_inputs
    assert fast.all_hits == reference.hits, ('full_reference_counts', folder)
    assert dict(fast.hits) == report['primary']['counts'], ('saved_counts', folder)
    # WB-off/PMP-only checks are deliberately different DUT configurations.
    # Current wb_pmp temporal exclusions must not be applied to them.
    assert profiles_seen <= {3}, 'This release audits only the fixed wb_pmp profile'
    excluded = {r['target']['id'] for r in artifacts.read_json(ROOT / 'targets/ibex/coverage/excluded.json')
                if True}
    contradictions = sorted(excluded & {k for k, v in reference.hits.items() if v})
    assert not contradictions, ('structural_exclusion_contradicted', contradictions)
    return dict(passed=True, rows=rows, hit=fast.report()['hit'], total=len(fast.records),
                source_model_declarations_observed=len(reference.observed),
                trace_sha256=artifacts.raw_sha256(folder / 'internal_trace.jsonl'),
                native_SV_coverage_database=False)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('directory', type=Path)
    args = parser.parse_args()
    result = {}
    union = set()
    for folder in sorted(p for p in args.directory.iterdir() if p.is_dir() and artifacts.exists(p/'internal_trace.jsonl')):
        result[folder.name] = audit(folder)
        report = artifacts.read_json(folder / 'report.json')
        union.update(k for k, v in report['primary']['counts'].items() if v)
    assert result, 'no full-plan traces'
    summary = dict(cases=len(result), passed=True, union_hit=len(union),
                   union_ids=sorted(union), audits=result)
    (args.directory / 'full_replay_audit.json').write_text(json.dumps(summary, indent=2))
    print(json.dumps({k: v for k, v in summary.items() if k not in ('audits', 'union_ids')}))


if __name__ == '__main__':
    main()
