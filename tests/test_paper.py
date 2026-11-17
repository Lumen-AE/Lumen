"""Behavioral boundary tests for the new optional paper components."""
from dataclasses import replace
import json
from pathlib import Path
import tempfile
import unittest
import z3
from lumen.paths import ROOT
from lumen.design.graph import build_graph, UnsupportedRTL
from lumen.design.knowledge import KnowledgeBase
from lumen.reasoning.temporal import Condition, Goal, TemporalModel, bind_and_decompose
from lumen.reasoning.binding import bind_bin
from lumen.paths import catalog_path
from lumen.observation.comparison import compare, compress, expand
from lumen.observation.selection import Probe, ProbeRegistry
from lumen.engine.budget import BudgetLedger
from lumen.engine.interfaces import Environment, Execution
from lumen.memory.records import PrefixStore, ExperienceStore


class TemporalSemanticsTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temporary = tempfile.TemporaryDirectory(prefix='lumen-semantic-')
        cls.root = Path(cls.temporary.name)
        cls.graph = build_graph([ROOT / 'examples/paper/semantics.sv'], 'semantics', cls.root / 'graph')

    @classmethod
    def tearDownClass(cls):
        cls.temporary.cleanup()

    def test_bitwidth_and_signedness_come_from_elaboration(self):
        model = TemporalModel(self.graph, 0)
        model.solver.add(model.signal('a', 0) == 15, model.signal('b', 0) == 1)
        self.assertEqual(model.check(), z3.sat)
        result = model.solver.model()
        self.assertEqual(result.eval(model.signal('sum', 0)).as_long(), 0)
        self.assertEqual(result.eval(model.signal('signed_less', 0)).as_long(), 1)
        self.assertEqual(result.eval(model.signal('unsigned_less', 0)).as_long(), 0)

    def test_register_crosses_one_edge_and_enable_holds(self):
        model = TemporalModel(self.graph, 1)
        model.solver.add(model.signal('rst_n', -1) == 1, model.signal('rst_n', 0) == 1,
                         model.signal('q', -1) == 7, model.signal('enable', -1) == 0)
        model.solver.add(model.signal('q', 0) != 7)
        self.assertEqual(model.check(), z3.unsat)

    def test_async_reset_has_priority_over_enable(self):
        model = TemporalModel(self.graph, 1)
        model.solver.add(model.signal('rst_n', 0) == 0, model.signal('enable', -1) == 1)
        model.solver.add(model.signal('q', 0) != 10)
        self.assertEqual(model.check(), z3.unsat)

    def test_sync_reset_is_previous_edge_and_wins_over_enable(self):
        model = TemporalModel(self.graph, 1)
        model.solver.add(model.signal('sync_reset', -1) == 1, model.signal('enable', -1) == 0)
        model.solver.add(model.signal('q_sync', 0) != 3)
        self.assertEqual(model.check(), z3.unsat)

    def test_mux_preserves_alternatives_without_inventing_a_selected_branch(self):
        goal = Goal('mux', ((Condition('selected', 5),),))
        model = TemporalModel(self.graph, 0)
        model.constrain_goal(goal)
        for select in (0, 1):
            model.solver.push()
            model.solver.add(model.signal('select', 0) == select)
            self.assertEqual(model.check(), z3.sat)
            model.solver.pop()
        plan = bind_and_decompose(self.graph, goal, 0, watched=['select', 'selected'])
        self.assertEqual([c['signal'] for c in plan['milestones'][0]['conditions']], ['selected'])

    def test_contradictory_same_frame_requirements_fail(self):
        goal = Goal('conflict', ((Condition('a', 1), Condition('a', 2)),))
        with self.assertRaises(ValueError):
            bind_and_decompose(self.graph, goal, 0)

    def test_missing_bin_bindings_and_sampling_gates_fail(self):
        record = next(r for r in json.loads(catalog_path().read_text())['targets'] if r['id'] == 'uarch_cg/cp_id_instr_category/0')
        with self.assertRaises(ValueError):
            bind_bin(record, self.graph, {})
        with self.assertRaises(ValueError):
            bind_bin(record, self.graph, {record['declaration']: 'enable'}, required_gate_ids=('valid',))

    def test_probe_width_and_sampling_phase_are_checked(self):
        with self.assertRaises(ValueError):
            ProbeRegistry(self.graph, [Probe('q', 'tb.dut.q', 1)])
        registry = ProbeRegistry(self.graph, [Probe('q', 'tb.dut.q', 4)])
        with self.assertRaises(ValueError):
            registry.project(dict(cycle=0, phase='post_edge', signals={'q': 0}), {'probes': []})

    def test_latch_is_explicitly_unsupported(self):
        file = self.root / 'latch.sv'
        file.write_text('module latch(input en,d, output reg q); always @* if(en) q=d; endmodule')
        with self.assertRaises(UnsupportedRTL):
            build_graph([file], 'latch', self.root / 'latch_graph')

    def test_unknown_rtl_constant_is_not_silently_zeroed(self):
        file = self.root / 'unknown.sv'
        file.write_text("module unknown(output wire q); assign q=1'bx; endmodule")
        with self.assertRaises(UnsupportedRTL):
            build_graph([file], 'unknown', self.root / 'unknown_graph')


class EvidenceAndStorageTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix='lumen-store-')
        self.root = Path(self.temporary.name)
        self.environment = Environment('rtl-v1', 'coverage-v1', {'width': 1}, {'reset': True}, {'memory': 'empty'}, None)

    def tearDown(self):
        self.temporary.cleanup()

    def test_missing_signal_is_unknown_and_monitor_is_authoritative(self):
        goal = Goal('b', ((Condition('a', 1), Condition('b', 1)),))
        evidence = compare(goal, [dict(cycle=1, phase='pre_edge_effective', signals={'a': 1})], {'b'})
        self.assertTrue(evidence['monitor_hit'])
        self.assertIsNone(evidence['predicate_match'])
        self.assertEqual(evidence['revision'], 'extend_observation')

    def test_individual_conditions_require_joint_cycle_hit(self):
        goal = Goal('b', ((Condition('a', 1), Condition('b', 1)),))
        trace = [dict(cycle=i, phase='pre_edge_effective', signals={'a': int(i == 0), 'b': int(i == 1)}) for i in range(2)]
        evidence = compare(goal, trace, set())
        self.assertFalse(evidence['monitor_hit'])
        self.assertFalse(evidence['predicate_match'])
        self.assertEqual(evidence['revision'], 'adjust_order_duration_or_spacing')

    def test_unknown_alternative_is_preserved(self):
        goal = Goal('b', ((Condition('a', 1),), (Condition('missing', 1),)))
        trace = [dict(cycle=0, phase='pre_edge_effective', signals={'a': 0})]
        evidence = compare(goal, trace, set())
        self.assertIsNone(evidence['predicate_match'])
        self.assertEqual(evidence['revision'], 'extend_observation')
        self.assertIn('missing', evidence['unexplained'])

    def test_compression_keeps_pulses_reset_handshake_and_duration(self):
        trace = [dict(cycle=i, phase='pre_edge_effective', signals={'q': 1}) for i in range(6)]
        trace[2]['events'] = ['pulse']
        trace[3]['reset_active'] = True
        trace[4]['handshake_accepted'] = True
        packed = compress(trace)
        self.assertEqual(expand(packed), trace)
        self.assertEqual(packed[0]['count'], 2)
        self.assertTrue(all(r['count'] == 1 for r in packed if r['protected']))

    def test_unknown_usage_and_invalid_attempt_are_accounted(self):
        ledger = BudgetLedger(self.root / 'budget.jsonl', max_tokens=100)
        ledger.charge_model({'input_tokens': 10, 'output_tokens': 5})
        ledger.charge_model(None)
        ledger.charge_execution(Execution(False, [], [], set(), 0, self.environment, False, error='invalid_json'))
        state = ledger.snapshot()
        self.assertEqual((state['model_calls'], state['known_tokens'], state['attempts']), (2, 15, 1))
        self.assertIsNone(state['total_tokens'])
        self.assertIn('token_budget_unverifiable', state['reasons'])

    def test_preparation_is_charged_and_bad_usage_does_not_mutate_counts(self):
        ledger = BudgetLedger(self.root / 'prep.jsonl', max_seconds=0.01)
        ledger.preparation(0.02)
        self.assertTrue(ledger.snapshot()['exhausted'])
        self.assertEqual(ledger.snapshot()['preparation_seconds'], 0.02)
        with self.assertRaises(ValueError):
            ledger.charge_model({'input_tokens': -1, 'output_tokens': 1})
        self.assertEqual(ledger.snapshot()['model_calls'], 0)

    def test_knowledge_missing_input_and_bad_source_span_fail(self):
        kb = KnowledgeBase(self.root / 'kb.sqlite')
        with self.assertRaises(FileNotFoundError):
            kb.ingest(self.root / 'missing', 'rtl', 'v1')
        file = self.root / 'source.sv'
        file.write_text('assign q = d;\n')
        item = kb.ingest(file, 'rtl', 'v1')
        with self.assertRaises(ValueError):
            kb.link(item, 'signal', 'q', 2, 3)
        kb.close()

    def test_unverified_or_incomplete_prefix_cannot_be_saved(self):
        store = PrefixStore(self.root / 'prefix')
        execution = Execution(True, [{'unit_fixture': 1}], [{'cycle': 0}], set(), 1, self.environment, True,
                              {'q': 1}, backend_receipt={'unit_fixture': True})
        with self.assertRaises(ValueError):
            store.store(execution, [Condition('q', 0)], 'bin')
        with self.assertRaises(ValueError):
            store.store(execution, [Condition('q', 1)], 'bin', complete_preparation=False)
        identifier = store.store(execution, [Condition('q', 1)], 'bin')
        self.assertEqual(store.compatible(self.environment, [Condition('q', 1)])[0]['id'], identifier)
        self.assertEqual(store.compatible(replace(self.environment, seed=1)), [])
        store.db.execute('UPDATE prefixes SET data=? WHERE id=?', ('{}', identifier))
        with self.assertRaises(ValueError):
            store.get(identifier)
        store.close()


if __name__ == '__main__':
    unittest.main()
