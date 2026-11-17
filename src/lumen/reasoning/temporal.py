"""Bind finite predicates and unroll actual register updates at effective edges."""
from dataclasses import asdict, dataclass
import json
import z3
from lumen.design.graph import COMBINATIONAL, REGISTERS, UnsupportedRTL, parameter


@dataclass(frozen=True)
class Condition:
    signal: str
    value: int
    offset: int = 0
    op: str = 'eq'

    def holds(self, values):
        actual = values.get(self.signal)
        if actual is None:
            return None
        if self.op == 'eq':
            return actual == self.value
        if self.op == 'ne':
            return actual != self.value
        raise ValueError('Unsupported predicate operator ' + self.op)


@dataclass(frozen=True)
class Goal:
    bin_id: str
    alternatives: tuple
    gates: tuple = ()
    phase: str = 'pre_edge_effective'

    @classmethod
    def from_dict(cls, data):
        if set(data) - {'bin_id', 'alternatives', 'gates', 'phase'}:
            raise ValueError('Unknown goal field')
        return cls(data['bin_id'], tuple(tuple(Condition(**c) for c in branch) for branch in data['alternatives']),
                   tuple(Condition(**c) for c in data.get('gates', [])), data.get('phase', 'pre_edge_effective'))

    def to_dict(self):
        return asdict(self)

    @property
    def conditions(self):
        return self.gates + tuple(c for branch in self.alternatives for c in branch)

    def validate(self, graph):
        if self.phase != 'pre_edge_effective' or not self.alternatives or any(not b for b in self.alternatives):
            raise ValueError('A goal requires explicit finite alternatives and pre-edge effective sampling')
        for item in self.conditions:
            width = len(graph.bits(item.signal))
            if item.op not in ('eq', 'ne') or not isinstance(item.offset, int) or item.offset > 0:
                raise ValueError('Unsupported condition')
            if type(item.value) is not int or not 0 <= item.value < 1 << width:
                raise ValueError('Value exceeds signal width')


def resize(value, width, signed=False):
    if value.size() < width:
        return (z3.SignExt if signed else z3.ZeroExt)(width - value.size(), value)
    return z3.Extract(width - 1, 0, value) if value.size() > width else value


class TemporalModel:
    def __init__(self, graph, horizon=2, timeout_ms=10000):
        if not isinstance(horizon, int) or not 0 <= horizon <= 64:
            raise ValueError('Bounded horizon must be in 0..64')
        self.graph, self.horizon = graph, horizon
        self.solver = z3.Solver()
        self.solver.set(timeout=timeout_ms)
        self.equations = []
        for cycle in range(-horizon, 1):
            for name, cell in graph.cells.items():
                relation = self.cell_equation(cell, cycle)
                if relation is not None:
                    self.solver.add(relation)
                    self.equations.append(dict(cell=name, cycle=cycle, kind=cell['type'],
                                               source=cell.get('attributes', {}).get('src'), formula=relation.sexpr()))

    def vector(self, bits, cycle):
        values = [z3.BitVecVal(int(bit), 1) if isinstance(bit, str) else z3.BitVec(f'b{bit}@{cycle}', 1) for bit in bits]
        return values[0] if len(values) == 1 else z3.Concat(*reversed(values))

    def signal(self, name, cycle):
        return self.vector(self.graph.bits(name), cycle)

    def atom(self, item):
        if item.op not in ('eq', 'ne') or type(item.value) is not int or type(item.offset) is not int:
            raise ValueError('Unsupported condition operator or type')
        if not -self.horizon <= item.offset <= 0:
            raise ValueError('Condition outside bounded horizon')
        value = self.signal(item.signal, item.offset)
        if not 0 <= item.value < 1 << value.size():
            raise ValueError('Condition value overflows graph width')
        return value == item.value if item.op == 'eq' else value != item.value

    def cell_equation(self, cell, t):
        ports, kind = cell['connections'], cell['type']
        vec = lambda p, cycle=t: self.vector(ports[p], cycle)
        if kind in REGISTERS:
            # Earliest state is unconstrained, apart from an active async reset.
            q = vec('Q')
            if t == -self.horizon:
                if 'ARST' in ports:
                    return z3.Implies(vec('ARST') == parameter(cell, 'ARST_POLARITY'), q == parameter(cell, 'ARST_VALUE'))
                return None
            previous = t - 1
            value = vec('D', previous)
            if 'EN' in ports:
                enabled = vec('EN', previous) == parameter(cell, 'EN_POLARITY')
                value = z3.If(enabled, value, vec('Q', previous))
            if 'SRST' in ports:
                active = vec('SRST', previous) == parameter(cell, 'SRST_POLARITY')
                if kind == '$sdffce':
                    active = z3.And(active, enabled)
                value = z3.If(active, z3.BitVecVal(parameter(cell, 'SRST_VALUE'), q.size()), value)
            if 'ARST' in ports:
                active = z3.Or(vec('ARST') == parameter(cell, 'ARST_POLARITY'),
                               vec('ARST', previous) == parameter(cell, 'ARST_POLARITY'))
                value = z3.If(active, z3.BitVecVal(parameter(cell, 'ARST_VALUE'), q.size()), value)
            return q == value
        y = vec('Y')
        a = vec('A')
        boolean = lambda condition: z3.If(condition, z3.BitVecVal(1, y.size()), z3.BitVecVal(0, y.size()))
        if kind == '$mux':
            return y == z3.If(vec('S') != 0, vec('B'), a)
        if kind == '$not':
            value = ~resize(a, y.size(), bool(parameter(cell, 'A_SIGNED')))
        elif kind == '$logic_not':
            value = boolean(a == 0)
        elif kind in ('$reduce_or', '$reduce_bool'):
            value = boolean(a != 0)
        elif kind == '$reduce_and':
            value = boolean(a == (1 << a.size()) - 1)
        elif kind in ('$reduce_xor', '$reduce_xnor'):
            bits = [z3.Extract(i, i, a) for i in range(a.size())]
            value = bits[0]
            for bit in bits[1:]:
                value = value ^ bit
            if kind == '$reduce_xnor':
                value = ~value
            value = resize(value, y.size())
        else:
            b = vec('B')
            signed = bool(parameter(cell, 'A_SIGNED') and parameter(cell, 'B_SIGNED'))
            width = max(a.size(), b.size(), y.size())
            a, b = resize(a, width, signed), resize(b, width, signed)
            operations = {'$and': lambda: a & b, '$or': lambda: a | b, '$xor': lambda: a ^ b,
                          '$xnor': lambda: ~(a ^ b), '$add': lambda: a + b, '$sub': lambda: a - b,
                          '$logic_and': lambda: boolean(z3.And(a != 0, b != 0)),
                          '$logic_or': lambda: boolean(z3.Or(a != 0, b != 0)),
                          '$eq': lambda: boolean(a == b), '$ne': lambda: boolean(a != b),
                          '$lt': lambda: boolean(a < b if signed else z3.ULT(a, b)),
                          '$le': lambda: boolean(a <= b if signed else z3.ULE(a, b)),
                          '$gt': lambda: boolean(a > b if signed else z3.UGT(a, b)),
                          '$ge': lambda: boolean(a >= b if signed else z3.UGE(a, b))}
            if kind not in operations:
                raise UnsupportedRTL('No temporal semantics for ' + kind)
            value = resize(operations[kind](), y.size())
        return y == value

    def constrain_goal(self, goal, assumptions=()):
        goal.validate(self.graph)
        self.solver.add(z3.Or(*(z3.And(*(self.atom(c) for c in branch)) for branch in goal.alternatives)))
        self.solver.add(*(self.atom(c) for c in goal.gates + tuple(assumptions)))

    def check(self):
        result = self.solver.check()
        if result == z3.unknown:
            raise TimeoutError('Temporal solver unresolved: ' + self.solver.reason_unknown())
        return result

    def forced_values(self, watched):
        if self.check() != z3.sat:
            raise ValueError('Target and assumptions are inconsistent within the bounded graph')
        witness = self.solver.model()
        milestones = []
        for t in range(-self.horizon, 1):
            conditions = []
            for name in watched:
                signal = self.signal(name, t)
                value = witness.eval(signal, model_completion=True).as_long()
                self.solver.push()
                self.solver.add(signal != value)
                forced = self.check() == z3.unsat
                self.solver.pop()
                if forced:
                    conditions.append(asdict(Condition(name, value, t)))
            milestones.append(dict(offset=t, conditions=conditions))
        return milestones


def bind_and_decompose(graph, goal, horizon=2, assumptions=(), watched=None):
    goal.validate(graph)
    model = TemporalModel(graph, horizon)
    model.constrain_goal(goal, assumptions)
    names = watched if watched is not None else [n for n in graph.signals if not n.startswith('$')]
    return dict(graph_sha256=graph.fingerprint, goal=goal.to_dict(), horizon=horizon,
                assumptions=[asdict(c) for c in assumptions], milestones=model.forced_values(names),
                update_equations=model.equations,
                semantics='bounded two-state pre-edge effective clock; branch/mux and reset relations retained',
                scope='necessary conditions under explicit assumptions, not a reachability proof for the complete DUT')
