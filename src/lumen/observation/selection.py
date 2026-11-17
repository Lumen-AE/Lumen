"""Optional graph-driven selection over predeclared read-only probe candidates."""
from dataclasses import asdict, dataclass
import re


@dataclass(frozen=True)
class Probe:
    node: str
    hierarchy: str
    width: int
    lsb: int = 0
    phase: str = 'pre_edge_effective'


class ProbeRegistry:
    def __init__(self, graph, probes):
        self.graph = graph
        self.probes = {}
        for probe in probes:
            if probe.node in self.probes or probe.width != len(graph.bits(probe.node)) or probe.lsb < 0:
                raise ValueError('Duplicate or width-mismatched probe')
            if not re.fullmatch(r'[A-Za-z_]\w*(?:\.[A-Za-z_]\w*)*', probe.hierarchy):
                raise ValueError('Unsupported hierarchy identifier')
            if probe.phase != 'pre_edge_effective':
                raise ValueError('Probe phase does not match the temporal graph')
            self.probes[probe.node] = probe

    def select(self, goal, depth=0, unmet=()):
        priority = sorted({c.signal for c in unmet})
        seeds = priority + sorted({c.signal for c in goal.conditions} - set(priority))
        cone = self.graph.cone(seeds, depth)
        missing = sorted(set(cone['signals']) - self.probes.keys())
        return dict(depth=depth, seeds=seeds, priority_seeds=priority, probes=[asdict(self.probes[n]) for n in cone['signals'] if n in self.probes],
                    unavailable=missing, register_boundaries=cone['register_boundaries'])

    def assignments(self, output_name='lumen_diagnostic_bus'):
        if not re.fullmatch('[A-Za-z_]\w*', output_name):
            raise ValueError('Invalid bus name')
        width = sum(p.width for p in self.probes.values())
        if not width:
            raise ValueError('No probe candidates')
        lines = [f'wire [{width - 1}:0] {output_name};']
        mapping, offset = [], 0
        for probe in self.probes.values():
            value = f'{probe.hierarchy}[{probe.lsb} +: {probe.width}]' if probe.width > 1 or probe.lsb else probe.hierarchy
            lines.append(f'assign {output_name}[{offset} +: {probe.width}] = {value};')
            mapping.append(dict(**asdict(probe), bus_offset=offset))
            offset += probe.width
        return '\n'.join(lines) + '\n', mapping

    def project(self, sample, selection):
        if sample.get('phase') != 'pre_edge_effective':
            raise ValueError('Wrong trace sampling phase')
        values, unknown = {}, []
        for item in selection['probes']:
            value = sample.get('signals', {}).get(item['node'])
            if value is None:
                unknown.append(item['node'])
            elif type(value) is not int or not 0 <= value < 1 << item['width']:
                raise ValueError('Probe value exceeds declared width')
            else:
                values[item['node']] = value
        return dict(cycle=sample['cycle'], phase=sample['phase'], values=values, unavailable=unknown)
