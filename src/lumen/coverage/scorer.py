"""Complete source-defined, per-instance official coverage on generated RTL probes."""
from collections import Counter
from functools import lru_cache
import itertools
import json
from .definitions import elaborate
from lumen.paths import catalog_path
from lumen.observation.probes import transactions
from lumen.observation.evidence import select_evidence


@lru_cache(maxsize=1)
def model():
    return elaborate()


@lru_cache(maxsize=1)
def compiled():
    definitions, _ = model()
    groups = {}
    for record in definitions.values():
        r = dict(record)
        if r['kind'] != 'cross':
            r['value_bins'] = {}
            r['transitions'] = []
            for b in r['bins']:
                if 'transition' in b:
                    r['transitions'].append(b)
                else:
                    for v in b['values']:
                        r['value_bins'].setdefault(v, []).append(b['label'])
        else:
            index = {}
            for b in r['bins']:
                for alternative in b.get('alternatives', [b]):
                    labels = tuple(alternative['dimensions'][d]['label'] for d in r['dimensions'])
                    index.setdefault(labels, []).append((b['label'], b.get('gate')))
            r['index'] = index
        groups.setdefault(r['group'], []).append(r)
    return groups


class FullCoverage:
    def __init__(self, catalog_name='official_current'):
        catalog = json.loads((catalog_path(catalog_name)).read_text())
        self.catalog_name = catalog_name
        self.records = {r['id']: r for r in catalog['targets']}
        self.hits = Counter({key: 0 for key in self.records})
        self.all_hits = Counter()
        self.witness = {}
        self.previous = {}
        self.first_error = self.second_pending = 0
        self.unknown_inputs = Counter()

    def reset_history(self):
        self.previous.clear()

    def sample(self, raw, cycle):
        if not raw['reset_n']:
            self.reset_history()
            return []
        if not raw['core_edge']:
            return []
        if 'official_bus' not in raw:
            raise ValueError('Full official scoring requires the generated RTL observer bus')
        new = []
        from lumen.observation.samples import FSM
        for (group, instance), transaction in transactions(raw['official_bus']).items():
            if group != 'uarch_cg' and not (raw['profile'] & 2):
                continue
            values, gates = transaction['values'], transaction['gates']
            active = {}
            suffix = '' if instance is None else '@' + str(instance)
            for r in compiled()[group]:
                if r['gate'] and r['id'] not in gates:
                    raise ValueError('Missing official gate: ' + r['id'])
                if r['gate'] and not gates[r['id']]:
                    if r['kind'] != 'cross':
                        active[r['name']] = []
                    continue
                if r['kind'] != 'cross':
                    value = values[r['name']]
                    matched = list(r['value_bins'].get(value, ()))
                    if r['transitions']:
                        current = FSM[value]
                        previous = self.previous.get(r['id'] + suffix)
                        matched += [b['label'] for b in r['transitions'] if [previous, current] == b['transition']]
                        self.previous[r['id'] + suffix] = current
                    active[r['name']] = matched
                else:
                    choices = [active[d] if d in active else [str(values[d])] for d in r['dimensions']]
                    matched = set()
                    for labels in itertools.product(*choices):
                        for label, gate in r['index'].get(labels, ()):
                            if gate is None or gates[r['id'] + '/' + label]:
                                matched.add(label)
                for label in matched:
                    key = r['id'] + '/' + label + suffix
                    self.all_hits[key] += 1
                    if key in self.records:
                        if not self.hits[key]:
                            new.append(key)
                            self.witness[key] = dict(cycle=cycle, official_bus=raw['official_bus'],
                                                     pc=raw['pc'], instruction=raw['instruction'])
                        self.hits[key] += 1
        return sorted(new)

    def evidence(self, target, rows, limit=64):
        record = self.records[target]
        return select_evidence(record, model()[0][record['declaration']], self.hits[target], target, rows, limit)

    def report(self):
        hit = sum(bool(v) for v in self.hits.values())
        total = len(self.records)
        return dict(kind='official_full_plan_python_per_instance', catalog=self.catalog_name,
                    hit=hit, total=total, percent=100 * hit / total if total else 0,
                    counts=dict(self.hits), missing=[k for k, v in self.hits.items() if not v])
