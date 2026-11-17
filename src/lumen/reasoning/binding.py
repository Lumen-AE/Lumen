"""Bind frozen finite-bin atoms to explicitly mapped graph signals."""
import itertools
from .temporal import Condition, Goal


def bind_bin(record, graph, signal_bindings, *, gate_conditions=(), required_gate_ids=(), gate_bindings=None, max_alternatives=4096):
    gates = list(gate_conditions)
    from lumen.coverage.scorer import model
    definitions = model()[0]
    if record['declaration'] not in definitions:
        raise ValueError('Unknown frozen declaration; use an explicit Goal for custom monitors')
    definition = definitions[record['declaration']]
    required = set(required_gate_ids)
    if definition['gate']:
        required.add(record['declaration'])
    for dimension in definition.get('dimensions', []):
        key = definition['group'] + '/' + dimension
        if key in definitions and definitions[key]['gate']:
            required.add(key)
    for branch in record['bin'].get('alternatives', [record['bin']]):
        if branch.get('gate'):
            required.add(record['declaration'] + '/' + record['bin']['label'])
    for gate in sorted(required):
        if not gate_bindings or gate not in gate_bindings:
            raise ValueError('Unbound sampling gate: ' + gate)
        gates.append(Condition(gate_bindings[gate], 1))
    alternatives = []
    for branch in record['bin'].get('alternatives', [record['bin']]):
        if 'transition' in branch:
            raise ValueError('Transition bins require an explicit offset Goal; no guessed temporal meaning')
        if 'dimensions' in branch:
            dimensions = branch['dimensions']
        else:
            dimensions = {record['declaration']: branch}
        choices = []
        for dimension, spec in dimensions.items():
            if dimension not in signal_bindings:
                raise ValueError('Unbound coverage variable: ' + dimension)
            if not spec.get('values') or any(type(v) is not int for v in spec['values']):
                raise ValueError('Only explicit finite numeric bin values are bound automatically')
            choices.append([Condition(signal_bindings[dimension], value) for value in spec['values']])
        for atoms in itertools.product(*choices):
            alternatives.append(atoms)
            if len(alternatives) > max_alternatives:
                raise ValueError('Finite predicate expansion exceeds the explicit limit')
    goal = Goal(record['id'], tuple(alternatives), tuple(gates))
    goal.validate(graph)
    return goal
