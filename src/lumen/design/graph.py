"""Strict word-level graph from real Yosys process-lowered JSON netlists."""
from dataclasses import dataclass
import hashlib
import json
from pathlib import Path
import re
import shutil
import subprocess


class UnsupportedRTL(ValueError):
    pass


COMBINATIONAL = {'$not', '$logic_not', '$and', '$or', '$xor', '$xnor', '$logic_and',
                 '$logic_or', '$eq', '$ne', '$lt', '$le', '$gt', '$ge', '$add', '$sub',
                 '$mux', '$reduce_or', '$reduce_bool', '$reduce_and', '$reduce_xor', '$reduce_xnor'}
REGISTERS = {'$dff', '$adff', '$dffe', '$adffe', '$sdff', '$sdffe', '$sdffce'}


def parameter(cell, name, default=0):
    value = cell.get('parameters', {}).get(name, default)
    if isinstance(value, str):
        if not re.fullmatch('[01]+', value):
            raise UnsupportedRTL('Unknown parameter bits: ' + name)
        return int(value, 2)
    return int(value)


@dataclass
class DesignGraph:
    top: str
    netlist: dict
    sources: list

    def __post_init__(self):
        modules = self.netlist.get('modules', {})
        if self.top not in modules:
            raise UnsupportedRTL('Missing elaborated top')
        self.module = modules[self.top]
        if self.module.get('memories') or self.module.get('processes'):
            raise UnsupportedRTL('Memory or unlowered process requires another frontend')
        self.cells = self.module['cells']
        self.signals = self.module['netnames']
        self.drivers, self.input_bits = {}, set()
        clocks = set()
        for name, port in self.module['ports'].items():
            if port['direction'] == 'inout':
                raise UnsupportedRTL('Bidirectional port: ' + name)
            if port['direction'] == 'input':
                self.input_bits.update(port['bits'])
        for name, cell in self.cells.items():
            kind = cell['type']
            if kind not in COMBINATIONAL | REGISTERS:
                raise UnsupportedRTL(f'Unsupported cell {kind} at {cell.get("attributes", {}).get("src", name)}')
            if kind in REGISTERS:
                if parameter(cell, 'CLK_POLARITY') != 1:
                    raise UnsupportedRTL('Only positive effective clock edges are supported')
                clock = tuple(cell['connections']['CLK'])
                if len(clock) != 1 or clock[0] not in self.input_bits:
                    raise UnsupportedRTL('Generated/gated clock must be abstracted as an explicit effective clock input')
                clocks.add(clock)
            for port, bits in cell['connections'].items():
                if any(isinstance(b, str) and b not in ('0', '1') for b in bits):
                    raise UnsupportedRTL('Four-state or undriven value in ' + name)
                if cell['port_directions'][port] == 'output':
                    for bit in bits:
                        if not isinstance(bit, int) or bit in self.drivers or bit in self.input_bits:
                            raise UnsupportedRTL('Constant, multiple or input driver')
                        self.drivers[bit] = name
        if len(clocks) > 1:
            raise UnsupportedRTL('Multiple clock domains are not supported')
        # Reject combinational cycles and unresolved drivers instead of inventing values.
        done, active = set(), set()
        def visit(bit):
            if isinstance(bit, str):
                if bit not in ('0', '1'):
                    raise UnsupportedRTL('Unknown wire constant')
                return
            if bit in done or bit in self.input_bits:
                return
            if bit not in self.drivers:
                raise UnsupportedRTL('Undriven bit ' + str(bit))
            name = self.drivers[bit]
            cell = self.cells[name]
            if cell['type'] in REGISTERS:
                done.add(bit)
                return
            if bit in active:
                raise UnsupportedRTL('Combinational cycle')
            active.add(bit)
            for port, bits in cell['connections'].items():
                if cell['port_directions'][port] == 'input':
                    for upstream in bits:
                        visit(upstream)
            active.remove(bit)
            done.add(bit)
        for signal in self.signals.values():
            for bit in signal['bits']:
                visit(bit)

    @property
    def fingerprint(self):
        return hashlib.sha256(json.dumps(self.to_dict(), sort_keys=True).encode()).hexdigest()

    def bits(self, signal):
        if signal not in self.signals:
            raise KeyError('Unbound graph signal: ' + signal)
        return self.signals[signal]['bits']

    def location(self, signal):
        return self.signals[signal].get('attributes', {}).get('src')

    def to_dict(self):
        return dict(top=self.top, netlist=self.netlist, sources=self.sources)

    def save(self, destination):
        Path(destination).write_text(json.dumps(self.to_dict(), indent=2), encoding='utf-8')

    @classmethod
    def load(cls, path):
        return cls(**json.loads(Path(path).read_text(encoding='utf-8')))

    def cone(self, signals, register_depth=0):
        """Walk all combinational edges; each further register costs one layer."""
        if register_depth < 0:
            raise ValueError('Negative register depth')
        visited, layers, boundaries = set(), {}, set()
        def walk(bit, depth):
            if isinstance(bit, str) or (bit in layers and layers[bit] <= depth):
                return
            visited.add(bit)
            layers[bit] = depth
            if bit not in self.drivers:
                return
            name = self.drivers[bit]
            cell = self.cells[name]
            register = cell['type'] in REGISTERS
            if register:
                boundaries.add(name)
            for port, bits in cell['connections'].items():
                if cell['port_directions'][port] != 'input' or port == 'CLK':
                    continue
                # Keep enable/reset controls at the boundary even at depth zero.
                if register and port == 'D' and depth >= register_depth:
                    continue
                for upstream in bits:
                    walk(upstream, depth + int(register))
        for signal in signals:
            for bit in self.bits(signal):
                walk(bit, 0)
        named = sorted(name for name, item in self.signals.items() if not name.startswith('$')
                       and any(isinstance(b, int) for b in item['bits'])
                       and all(isinstance(b, str) or b in visited for b in item['bits']))
        return dict(signals=named, bits=sorted(visited), register_boundaries=sorted(boundaries), depth=register_depth)


def build_graph(sources, top, output, executable='yowasp-yosys'):
    """Compile SystemVerilog through a real frontend; unsupported output fails closed."""
    if not re.fullmatch('[A-Za-z_][A-Za-z0-9_]*', top):
        raise ValueError('Invalid top module name')
    output = Path(output)
    output.mkdir(parents=True, exist_ok=False)
    records, copies = [], []
    for index, source in enumerate(sources):
        source = Path(source)
        data = source.read_bytes()
        name = f'input_{index}.sv'
        (output / name).write_bytes(data)
        records.append(dict(file=name, original_name=source.name, sha256=hashlib.sha256(data).hexdigest()))
        copies.append(name)
    if not copies:
        raise ValueError('No source files')
    tool = shutil.which(executable)
    if not tool:
        raise RuntimeError('Install requirements-paper.txt or provide a Yosys executable')
    script = 'read_verilog -sv ' + ' '.join(copies) + f'; hierarchy -check -top {top}; proc; flatten; opt_muxtree; opt_expr -keepdc; opt_merge; opt_clean; write_json netlist.json'
    (output / 'build.ys').write_text(script + '\n')
    result = subprocess.run([tool, '-s', 'build.ys'], cwd=output, capture_output=True, text=True, timeout=240)
    (output / 'frontend.log').write_text(result.stdout + result.stderr)
    if result.returncode:
        raise UnsupportedRTL('RTL frontend failed; inspect ' + str(output / 'frontend.log'))
    graph = DesignGraph(top, json.loads((output / 'netlist.json').read_text()), records)
    graph.save(output / 'graph.json')
    return graph
