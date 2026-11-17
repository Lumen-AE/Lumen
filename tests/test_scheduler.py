import unittest
from lumen.engine.scheduler import TargetController
from lumen.engine.feedback import public_feedback


class AssignedTargetTests(unittest.TestCase):
    def feedback(self, *hit):
        return dict(coverage=dict(counts={key: int(key in hit) for key in ('a', 'b', 'c')}))

    def test_incidental_new_bins_do_not_extend_assigned_target_budget(self):
        controller = TargetController(['a', 'b', 'c'])
        first = controller.accept(self.feedback('b'))
        self.assertFalse(first['advance'])
        self.assertEqual(controller.misses, 1)
        second = controller.accept(self.feedback('b', 'c'))
        self.assertTrue(second['advance'])
        self.assertTrue(controller.finished)
        self.assertEqual(controller.stop_reason, 'all_targets_attempted')
        self.assertEqual(controller.report()['hit'], 2)
        self.assertEqual(controller.records[0]['outcome'], 'two_target_misses')
        self.assertEqual(controller.records[0]['attempts'], 2)

    def test_assigned_hit_advances_and_keeps_union(self):
        controller = TargetController(['a', 'b', 'c'])
        controller.accept(self.feedback('a', 'c'))
        self.assertEqual(controller.current, 'b')
        controller.accept(self.feedback('a', 'b', 'c'))
        self.assertEqual(controller.stop_reason, 'all_bins_covered')
        self.assertEqual(controller.report()['percent'], 100)

    def test_invalid_response_still_costs_attempt_and_preserves_incidental_hits(self):
        controller = TargetController(['a', 'b', 'c'])
        bad = self.feedback('b')
        bad['error'] = 'not JSON'
        controller.accept(bad)
        self.assertEqual(controller.attempts, 1)
        controller.accept(bad)
        self.assertEqual(controller.current, 'c')
        self.assertEqual(controller.report()['hit'], 1)

    def test_base_view_removes_evidence_and_full_private_count_map(self):
        controller = TargetController(['a', 'b', 'c'])
        fb = self.feedback()
        fb['evidence'] = dict(trace=[dict(cycle=1, value=3)])
        catalog = {k: dict(id=k) for k in ('a', 'b', 'c')}
        base = public_feedback(fb, controller, catalog, 'baseline')
        evidence = public_feedback(fb, controller, catalog, 'evidence')
        self.assertNotIn('counts', base['coverage'])
        self.assertNotIn('evidence', base)
        self.assertEqual(evidence.pop('evidence'), fb['evidence'])
        self.assertEqual(base, evidence)

    def test_later_incidental_hit_recovers_earlier_failed_target_in_union(self):
        controller = TargetController(['a', 'b', 'c'])
        controller.accept(self.feedback('b'))
        controller.accept(self.feedback('b'))
        self.assertEqual(controller.current, 'c')
        controller.accept(self.feedback('a', 'b', 'c'))
        self.assertEqual(controller.records[0]['outcome'], 'two_target_misses')
        self.assertEqual(controller.report()['percent'], 100)

    def test_evidence_seed_skips_baseline_hits_keeps_full_denominator(self):
        controller = TargetController(['a', 'b', 'c'], initial_covered=['a'])
        self.assertEqual(controller.current, 'b')
        controller.accept(self.feedback('b'))
        self.assertEqual(controller.current, 'c')
        self.assertEqual(controller.report()['total'], 3)
        self.assertEqual(controller.report()['additional_hit'], 1)
        controller.accept(self.feedback('b', 'c'))
        self.assertEqual(controller.report()['percent'], 100)

    def test_seed_cannot_add_unknown_bins(self):
        with self.assertRaises(ValueError):
            TargetController(['a', 'b', 'c'], initial_covered=['wrong'])

    def test_seed_and_incidental_hits_do_not_extend_two_misses(self):
        controller = TargetController(['a', 'b', 'c'], initial_covered=['a'])
        controller.accept(self.feedback('c'))
        controller.accept(self.feedback('c'))
        self.assertTrue(controller.finished)
        self.assertEqual(controller.report()['hit'], 2)
        self.assertEqual(controller.records[1]['outcome'], 'two_target_misses')


if __name__ == '__main__':
    unittest.main()
