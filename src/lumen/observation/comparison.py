"""Measured condition/timing comparisons, independent of authoritative monitor hits."""
from dataclasses import asdict
from lumen.reasoning.temporal import Condition, Goal


def _at(condition, effective, anchor):
    index = anchor + condition.offset
    row = effective[index] if 0 <= index < len(effective) else None
    actual = None if row is None else row.get('signals', {}).get(condition.signal)
    matched = None if actual is None else condition.holds({condition.signal: actual})
    return dict(**asdict(condition), cycle=None if row is None else row['cycle'], actual=actual, matched=matched)


def _conjunction(checks):
    if any(c['matched'] is False for c in checks):
        return False
    return None if any(c['matched'] is None for c in checks) else True


def compare(goal, trace, monitor_hits, milestones=(), anchor_cycle=None):
    cycles = [row['cycle'] for row in trace]
    if cycles != sorted(set(cycles)):
        raise ValueError('Trace cycles must be unique and increasing')
    effective = [r for r in trace if r.get('core_edge', True) and r.get('phase') == goal.phase]
    if not effective:
        return dict(target=goal.bin_id, monitor_hit=goal.bin_id in monitor_hits, predicate_match=None,
                    first_deviation=None, unexplained=['no matching effective sampling phase'], revision='extend_observation', checks=[])
    if anchor_cycle is not None:
        anchors = [i for i, row in enumerate(effective) if row['cycle'] == anchor_cycle]
        if not anchors:
            raise ValueError('Requested anchor is not an effective sample')
    else:
        anchors = range(len(effective))
    selected = None
    for anchor in anchors:
        gate_checks = [_at(c, effective, anchor) for c in goal.gates]
        branches = [[_at(c, effective, anchor) for c in branch] for branch in goal.alternatives]
        status = [_conjunction(gate_checks + branch) for branch in branches]
        match = True if True in status else None if None in status else False
        branch = status.index(True) if True in status else status.index(None) if None in status else 0
        selected = (anchor, match, gate_checks + branches[branch])
        if match is True:
            break
    anchor, match, checks = selected
    for item in milestones:
        condition = Condition(**item)
        if asdict(condition) not in [dict((k, row[k]) for k in ('signal', 'value', 'offset', 'op')) for row in checks]:
            checks.append(_at(condition, effective, anchor))
    ordered = sorted(checks, key=lambda row: (row['offset'], row['signal']))
    deviations = [row for row in ordered if row['matched'] is not True]
    unknown = sorted({row['signal'] for row in checks if row['matched'] is None})
    seen = lambda c: any(c.holds(r.get('signals', {})) is True for r in effective)
    separate = all(seen(c) for c in goal.gates) and any(all(seen(c) for c in branch) for branch in goal.alternatives)
    if unknown:
        revision = 'extend_observation'
    elif match is not True and separate:
        revision = 'adjust_order_duration_or_spacing'
    elif any(r.get('handshake_requested') and not r.get('handshake_accepted') for r in trace):
        revision = 'adjust_flow_control'
    elif match is not True:
        revision = 'repair_preparation_or_wait_condition'
    else:
        revision = 'monitor_confirmation' if goal.bin_id in monitor_hits else 'inspect_monitor_binding'
    return dict(target=goal.bin_id, phase=goal.phase, anchor_cycle=effective[anchor]['cycle'],
                monitor_hit=goal.bin_id in monitor_hits, predicate_match=match,
                first_deviation=deviations[0] if deviations else None, unexplained=unknown,
                checks=ordered, revision=revision, monitor_hits=sorted(monitor_hits))


def window(trace, center_cycle, before=3, after=3):
    if before < 0 or after < 0:
        raise ValueError('Negative window')
    if not trace:
        return []
    index = min(range(len(trace)), key=lambda i: abs(trace[i]['cycle'] - center_cycle))
    return trace[max(0, index - before):index + after + 1]


def compress(trace):
    """Lossless consecutive run-length encoding, never coalescing protected events."""
    result = []
    for row in trace:
        sample = {k: v for k, v in row.items() if k != 'cycle'}
        protected = bool(row.get('events') or row.get('handshake_accepted') or row.get('reset_active'))
        if (result and not protected and not result[-1]['protected'] and result[-1]['sample'] == sample
                and result[-1]['end_cycle'] + 1 == row['cycle']):
            result[-1]['count'] += 1
            result[-1]['end_cycle'] = row['cycle']
        else:
            result.append(dict(start_cycle=row['cycle'], end_cycle=row['cycle'], count=1, sample=sample, protected=protected))
    return result


def expand(segments):
    rows = []
    for segment in segments:
        if segment['count'] != segment['end_cycle'] - segment['start_cycle'] + 1:
            raise ValueError('Invalid compressed duration')
        rows.extend(dict(cycle=cycle, **segment['sample']) for cycle in range(segment['start_cycle'], segment['end_cycle'] + 1))
    return rows


class EvidenceJudge:
    def __init__(self, goals, plans=None):
        self.goals, self.plans = goals, plans or {}

    def evaluate(self, target, execution, previous=()):
        if not execution.valid:
            return dict(target=target, valid=False, error=execution.error, monitor_hit=False,
                        revision='repair_interface_or_prefix', unexplained=[execution.error])
        plan = self.plans.get(target, {})
        milestones = [c for m in plan.get('milestones', []) for c in m['conditions']]
        evidence = compare(self.goals[target], execution.trace, execution.monitor_hits, milestones)
        deviation = evidence.get('first_deviation')
        center = deviation.get('cycle') if deviation else evidence.get('anchor_cycle')
        center = evidence.get('anchor_cycle', execution.trace[-1]['cycle'] if execution.trace else 0) if center is None else center
        evidence['window'] = compress(window(execution.trace, center))
        evidence['valid'] = True
        return evidence
