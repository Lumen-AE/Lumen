"""Executable source-derived graph, three-frame decomposition and knowledge example."""
import argparse
import json
from pathlib import Path
import time
from lumen.paths import IBEX, FCOV, catalog_path
from lumen.design.graph import build_graph
from lumen.design.knowledge import KnowledgeBase
from lumen.reasoning.binding import bind_bin
from lumen.reasoning.temporal import Condition, bind_and_decompose
from lumen.observation.selection import Probe, ProbeRegistry
from lumen.engine.budget import BudgetLedger
from examples.paper.build_debug_slice import extract


DEBUG_BIN = 'uarch_cg/debug_entry_if_instr_cross/cp_debug_entry_if=seen|instr_unstalled_last=1|cp_id_instr_category_last=16'


def run(output):
    output = Path(output)
    output.mkdir(parents=True, exist_ok=False)
    started = time.monotonic()
    source = extract(output / 'source')
    graph = build_graph([source], 'debug_slice', output / 'frontend')
    record = next(row for row in json.loads(catalog_path().read_text())['targets'] if row['id'] == DEBUG_BIN)
    goal = bind_bin(record, graph, {'cp_debug_entry_if': 'debug_entry_if', 'instr_unstalled_last': 'instr_unstalled_last',
                                  'cp_id_instr_category_last': 'id_instr_category_last'}, gate_conditions=(Condition('rst_ni', 1),))
    assumptions = tuple(c for t in range(-2, 1) for c in (Condition('rst_ni', 1, t), Condition('decoded_category', 16, t, 'ne')))
    watched = ['instr_valid_id_q', 'stall', 'new_input', 'flush_id', 'instr_valid_clear_i', 'id_stall_type',
               'instr_unstalled', 'id_instr_category', 'instr_unstalled_last', 'id_instr_category_last', 'debug_entry_if']
    plan = bind_and_decompose(graph, goal, 2, assumptions, watched)
    forced = {(item['signal'], item['offset']): item['value'] for m in plan['milestones'] for item in m['conditions']}
    expected = {('instr_valid_id_q', -2): 1, ('stall', -2): 1, ('new_input', -2): 0, ('flush_id', -2): 1,
                ('instr_valid_id_q', -1): 0, ('id_stall_type', -1): 0, ('instr_unstalled', -1): 1,
                ('id_instr_category', -1): 16, ('instr_unstalled_last', 0): 1,
                ('id_instr_category_last', 0): 16, ('debug_entry_if', 0): 1}
    for key, value in expected.items():
        assert forced.get(key) == value, (key, forced.get(key), value)
    (output / 'temporal_plan.json').write_text(json.dumps(plan, indent=2))
    registry = ProbeRegistry(graph, [Probe(name, 'tb.dut.' + name, len(graph.bits(name)))
                                    for name in graph.signals if not name.startswith('$')])
    selections = [registry.select(goal, depth) for depth in range(3)]
    assert set(p['node'] for p in selections[0]['probes']) < set(p['node'] for p in selections[1]['probes'])
    assert set(p['node'] for p in selections[1]['probes']) <= set(p['node'] for p in selections[2]['probes'])
    text, probes = registry.assignments()
    (output / 'candidate_probes.svh').write_text(text)
    (output / 'observers.json').write_text(json.dumps(dict(candidates=probes, selections=selections), indent=2))
    knowledge = KnowledgeBase(output / 'design.sqlite')
    docs = [
        ('design', IBEX / 'coverage/reference/ibex/doc/03_reference/coverage_plan.rst'),
        ('isa', IBEX / 'coverage/reference/ibex/rtl/ibex_pkg.sv'),
        ('coverage', FCOV / 'core_ibex_fcov_if.sv'),
        ('rtl', IBEX / 'rtl/lowrisc_ibex_ibex_core_0.1/rtl/ibex_if_stage.sv')]
    ids = {kind: knowledge.ingest(path, kind, 'pinned-source-sha256') for kind, path in docs}
    knowledge.link(ids['coverage'], 'bin', DEBUG_BIN, record['line'], record['line'] + 1)
    knowledge.link(ids['rtl'], 'signal', 'instr_valid_id_q', 477, 491)
    knowledge.link(ids['rtl'], 'node', 'debug_slice.instr_valid_id_q', 477, 491)
    queried = dict(bin=knowledge.query(entity_type='bin', entity=DEBUG_BIN),
                   signal=knowledge.query(entity_type='signal', entity='instr_valid_id_q'),
                   isa=knowledge.query('OPCODE_LOAD', kind='isa'))
    assert queried['bin'] and queried['signal'] and queried['isa']
    knowledge.close()
    (output / 'knowledge_queries.json').write_text(json.dumps(queried, indent=2))
    measured = time.monotonic() - started
    costs = BudgetLedger(output / 'preparation_costs.jsonl')
    costs.preparation(measured)
    receipt = dict(passed=True, graph_sha256=graph.fingerprint, graph_cells=len(graph.cells),
                   source_mapping=True, debug_three_frame_implications=True,
                   selected_probes=[len(s['probes']) for s in selections], knowledge_kinds=list(ids),
                   measured_preparation_seconds=measured, actual_costs=costs.snapshot(),
                   scope='actual source-derived cone under declared cutpoint assumptions; not full-Ibex reachability')
    (output / 'receipt.json').write_text(json.dumps(receipt, indent=2))
    print(json.dumps(receipt, indent=2), flush=True)
    return receipt


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--output', type=Path, required=True)
    run(parser.parse_args().output)
