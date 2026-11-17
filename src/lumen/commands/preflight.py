"""Check the relocated P2 runtime without historical experiment artifacts."""
import hashlib
import json
from pathlib import Path
import sys

from lumen.paths import ROOT
from lumen.engine.config import load_config
from lumen.coverage.scorer import FullCoverage, model
from lumen.observation.probes import observer_map


def check():
    config, catalog = load_config()
    assert config['denominator'] == catalog['total'] == len(catalog['targets']) == 3832
    assert config['cycles_per_attempt'] == 256 and config['consecutive_target_misses'] == 2
    assert json.loads((ROOT / 'profiles/ibex.json').read_text())['wb_pmp'] == dict(
        WritebackStage=1, PMPEnable=1, PMPNumRegions=4, ICache=0, SecureIbex=0)
    definitions, bins = model()
    excluded = json.loads((ROOT / 'targets/ibex/coverage/excluded.json').read_text())
    all_ids = {b['id'] + ('@' + str(i) if b['group'] == 'pmp_region_cg' else '')
               for b in bins for i in (range(4) if b['group'] == 'pmp_region_cg' else (None,))}
    selected = {r['id'] for r in catalog['targets']}
    removed = {r['target']['id'] for r in excluded}
    assert len(all_ids) == 4814 and len(removed) == 982
    assert selected.isdisjoint(removed) and selected | removed == all_ids
    by_id = {b['id']: b for b in bins}
    for row in catalog['targets'] + [r['target'] for r in excluded]:
        for key in ('declaration', 'bin', 'group', 'kind', 'file', 'line'):
            assert row[key] == by_id[row['type_id']][key], (row['id'], key)
    mapping = observer_map()
    fcov = ROOT / 'targets/ibex/coverage/reference/ibex/dv/uvm/core_ibex/fcov'
    for filename, expected in mapping['sources'].items():
        assert hashlib.sha256((fcov / filename).read_bytes()).hexdigest() == expected
    groups = {}
    for probe in mapping['probes']:
        group = groups.setdefault((probe['group'], probe['instance']), dict(values=set(), gates=set()))
        group['values' if probe['kind'] == 'value' else 'gates'].add(probe['key'])
    for r in definitions.values():
        for instance in (range(4) if r['group'] == 'pmp_region_cg' else (None,)):
            bound = groups[(r['group'], instance)]
            assert r['kind'] == 'cross' or r['name'] in bound['values']
            assert not r['gate'] or r['id'] in bound['gates']
            if r['kind'] == 'cross':
                assert set(r['dimensions']) <= bound['values']
            for b in r['bins']:
                assert not b.get('gate') or r['id'] + '/' + b['label'] in bound['gates']
    from lumen.paths import public_files, PUBLIC
    for arm in ('base', 'evidence'):
        assert all(path.is_file() for _, path in public_files(arm))
    assert [p for _, p in public_files('base')][1:] == [p for _, p in public_files('evidence')][1:]
    assert (PUBLIC / 'targets.json').is_file()
    assert FullCoverage().report()['total'] == 3832
    seal = json.loads((ROOT / 'SOURCE_MANIFEST.json').read_text())
    for row in seal['files']:
        assert hashlib.sha256((ROOT / row['path']).read_bytes()).hexdigest() == row['sha256'], ('release source changed', row['path'])
    return dict(passed=True, denominator=3832, excluded=982, declarations=len(definitions),
                complete_probe_binding=True, public_inputs_identical=True, sealed_files=len(seal['files']),
                historical_witness_archive_required=False)


if __name__ == '__main__':
    print(json.dumps(check(), indent=2))
