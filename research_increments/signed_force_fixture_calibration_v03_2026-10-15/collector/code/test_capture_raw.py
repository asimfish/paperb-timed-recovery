"""Meaningful shared-buffer lifetime and refusal probes, all SDK-free."""
import copy
import math
import unittest
from capture_raw import selected_copy, query_contact, observed, canonical


class Array:
    def __init__(self, values, shape):
        self.values, self.shape = values, shape
    def tolist(self):
        return copy.deepcopy(self.values)
    def __getitem__(self, index):
        value = self.values[index]
        if value is None:
            raise AssertionError('UNUSED_SLOT_READ')
        return copy.deepcopy(value)


def buffers(force=-2.0):
    return [Array([[force], None, None], (3, 1)),
        Array([[1.0, 2.0, 3.0], None, None], (3, 3)),
        Array([[0.0, 0.0, 1.0], None, None], (3, 3)),
        Array([[0.0], None, None], (3, 1)),
        Array([[1]], (1, 1)), Array([[0]], (1, 1))]


class CaptureTests(unittest.TestCase):
    def test_signed_and_unused_preserved(self):
        out = selected_copy(buffers(), kind='normal', sensors=1, filters=1, capacity=3)
        self.assertEqual(out['forces'], [[-2.0], None, None])
        self.assertEqual(out['selected_slot_indices'], [0])
        self.assertFalse(out['capacity_saturated'])
    def test_negative_zero_not_rewritten(self):
        out = selected_copy(buffers(-0.0), kind='normal', sensors=1, filters=1, capacity=3)
        self.assertEqual(math.copysign(1, out['forces'][0][0]), -1)
    def test_copied_counts_survive_reuse(self):
        raw = buffers(); out = selected_copy(raw, kind='normal', sensors=1, filters=1, capacity=3)
        raw[-2].values[0][0] = 0; raw[0].values[0][0] = 3
        self.assertEqual(out['counts'], [[1]]); self.assertEqual(out['forces'][0], [-2.0])
    def test_range_refused(self):
        raw = buffers(); raw[-2].values = [[4]]
        with self.assertRaisesRegex(ValueError, 'SELECTED_RANGE'):
            selected_copy(raw, kind='normal', sensors=1, filters=1, capacity=3)
    def test_bool_count_refused(self):
        raw = buffers(); raw[-2].values = [[True]]
        with self.assertRaises(ValueError):
            selected_copy(raw, kind='normal', sensors=1, filters=1, capacity=3)
    def test_nonfinite_selected_refused(self):
        raw = buffers(float('nan'))
        with self.assertRaisesRegex(ValueError, 'NONFINITE'):
            selected_copy(raw, kind='normal', sensors=1, filters=1, capacity=3)
    def test_arity_refused(self):
        with self.assertRaisesRegex(ValueError, 'ARITY'):
            selected_copy(buffers()[:5], kind='normal', sensors=1, filters=1, capacity=3)
    def test_overlap_refused(self):
        raw = buffers(); raw[-2] = Array([[1, 1]], (1, 2)); raw[-1] = Array([[0, 0]], (1, 2))
        with self.assertRaisesRegex(ValueError, 'OVERLAPPING'):
            selected_copy(raw, kind='normal', sensors=1, filters=2, capacity=3)
    def test_observed_missing_not_zero(self):
        def fail():
            raise RuntimeError('getter unavailable')
        row = observed(lambda: {'callback': 1}, fail)
        self.assertEqual(row['status'], 'UNKNOWN'); self.assertIsNone(row['value'])
    def test_observed_clock_change_explicit(self):
        values = iter([{'callback': 1}, {'callback': 2}])
        row = observed(lambda: next(values), lambda: [1.0])
        self.assertFalse(row['no_step_during_getter'])
    def test_freefall_details_never_called(self):
        class View:
            def get_net_contact_forces(self, dt):
                return [[0.0, 0.0, 0.0]]
        out = query_contact(View(), 1.0, lambda: {'clock': 1}, False)
        self.assertNotIn('normal_detail', out)
        self.assertEqual(out['channel_scope'], 'INTENTIONALLY_NOT_CONFIGURED_FREEFALL')
    def test_normal_copied_before_friction_reuses_counts(self):
        raw = buffers()
        class View:
            sensor_count = 1; filter_count = 1; max_contact_data_count = 3
            def get_net_contact_forces(self, dt): return [[0.0, 0.0, -2.0]]
            def get_contact_force_matrix(self, dt): return [[[0.0, 0.0, -2.0]]]
            def get_contact_data(self, dt): return raw
            def get_friction_data(self, dt):
                raw[-2].values = [[0]]
                return [Array([None] * 3, (3, 3)), Array([None] * 3, (3, 3)), raw[-2], raw[-1]]
        out = query_contact(View(), 1.0, lambda: {'clock': 1}, True)
        self.assertEqual(out['normal_detail']['value']['counts'], [[1]])
        self.assertEqual(out['friction_detail']['value']['counts'], [[0]])


if __name__ == '__main__':
    unittest.main()
