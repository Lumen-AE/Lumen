"""Opt-in Initial/Refine orchestration, separate from historical base/evidence."""
from lumen.reasoning.temporal import Condition


class FixedScheduler:
    def __init__(self, targets):
        self.targets = list(targets)
        if len(set(self.targets)) != len(self.targets):
            raise ValueError('Duplicate target order')
        self.index = 0

    def next_target(self, covered):
        while self.index < len(self.targets):
            target = self.targets[self.index]
            self.index += 1
            if target not in covered:
                return target
        return None


def run_two_pass(targets, generator, backend, judge, experiences, prefixes, ledger,
                 *, registry=None, goals=None, plans=None, knowledge=None,
                 arrival_conditions=None, limits=(2, 2), scheduler_factory=FixedScheduler):
    """Only monitor hits change coverage; prefix mismatch cannot authorize a suffix."""
    targets = list(targets)
    if len(limits) != 2 or any(type(n) is not int or n <= 0 for n in limits):
        raise ValueError('Two positive pass limits required')
    coverage, evidence = set(), {target: [] for target in targets}
    depth = {target: 0 for target in targets}
    history = []
    arrivals = arrival_conditions or {}
    for phase, limit in zip(('Initial', 'Refine'), limits):
        scheduler = scheduler_factory(targets)
        while (target := scheduler.next_target(coverage)) is not None:
            for attempt in range(1, limit + 1):
                if target in coverage or ledger.snapshot()['exhausted']:
                    break
                selection = registry.select(goals[target], depth[target]) if registry else dict(depth=depth[target], probes=[], unavailable=[])
                required = arrivals.get(target, ())
                candidates = prefixes.compatible(backend.environment, required) if required else []
                context = dict(target=target, phase=phase, attempt=attempt, evidence=evidence[target],
                               experience=experiences.find(target), observers=selection,
                               prefixes=candidates, environment=backend.environment.fingerprint,
                               goal=goals[target].to_dict() if goals else None,
                               plan=(plans or {}).get(target),
                               knowledge=knowledge.query(entity_type='bin', entity=target) if knowledge else [])
                generated = generator.generate(context)
                for usage in generated.usage:
                    ledger.charge_model(usage)
                if ledger.snapshot()['exhausted']:
                    break
                if generated.prefix_id:
                    if generated.prefix_id not in {r['id'] for r in candidates}:
                        raise ValueError('Generator chose a prefix incompatible with the requested preparation')
                    result = prefixes.replay(generated.prefix_id, backend, generated.actions, selection['probes'])
                else:
                    result = backend.execute(generated.actions, observers=selection['probes'])
                ledger.charge_execution(result)
                assessed = judge.evaluate(target, result, evidence[target])
                evidence[target].append(assessed)
                experiences.add(target, result, assessed)
                stored = None
                if result.valid:
                    if not result.monitor_hits <= set(targets):
                        # Other real bins can exist; scheduler only owns the supplied fixed target set.
                        coverage.update(result.monitor_hits & set(targets))
                    else:
                        coverage.update(result.monitor_hits)
                    arrival = required
                    if not arrival and target in result.monitor_hits:
                        arrival = tuple(Condition(k, v) for k, v in result.state.items() if type(v) is int)
                    if arrival and all(c.holds(result.state) is True for c in arrival):
                        stored = prefixes.store(result, arrival, target)
                if result.valid and target not in coverage:
                    depth[target] += 1
                history.append(dict(phase=phase, target=target, attempt=attempt, depth=selection['depth'],
                                    valid=result.valid, prefix_used=generated.prefix_id, prefix_stored=stored,
                                    monitor_hits=sorted(result.monitor_hits), revision=assessed.get('revision')))
            if ledger.snapshot()['exhausted']:
                break
        if ledger.snapshot()['exhausted']:
            break
    return dict(covered=sorted(coverage), remaining=[t for t in targets if t not in coverage],
                evidence=evidence, observation_depth=depth, history=history, costs=ledger.snapshot())
