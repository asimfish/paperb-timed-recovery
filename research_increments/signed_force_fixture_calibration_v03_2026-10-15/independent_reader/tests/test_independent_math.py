import copy
import math
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "code"))
from independent_math import (Rejected, acceleration, detail_matrix_agreement,
                              dt_consistency, freefall, low_motion, reciprocal,
                              signed_pair_sum, static_top)


class IndependentMathTests(unittest.TestCase):
    def test_selected_negative_is_valid_product_without_abs(self):
        points = [{"scalar": -0.981, "normal": [0, 0, -1]}]
        self.assertEqual(signed_pair_sum(points), [0, 0, 0.981])
        self.assertEqual(detail_matrix_agreement(points, [0, 0, 0.981]), 0)
        points[0]["scalar"] = abs(points[0]["scalar"])
        with self.assertRaisesRegex(Rejected, "vector error"):
            detail_matrix_agreement(points, [0, 0, 0.981])

    def test_gravity_is_freefall_oracle_not_zero_acceleration(self):
        a = acceleration([0, 0, -9.81/240], [0, 0, 0], 1/240)
        freefall(a, [0, 0, -9.81], [0, 0, 0])
        with self.assertRaises(Rejected):
            freefall([0, 0, 0], [0, 0, -9.81], [0, 0, 0])
        with self.assertRaises(Rejected):
            low_motion([0, 0, 0], [0, 0, 0], a, [0, 0, 0])

    def test_support_rotation_and_mass_use_world_gravity(self):
        static_top(.1, [0, 0, 0], [-9.81, 0, 0], [.981, 0, 0], [.981, 0, 0], [0, 0, 0])
        static_top(.2, [0, 0, 0], [0, 0, -9.81], [0, 0, 1.962], [0, 0, 1.962], [0, 0, 0])
        with self.assertRaises(Rejected):
            static_top(.1, [0, 0, 0], [-9.81, 0, 0], [0, 0, .981], [0, 0, .981], [0, 0, 0])
        with self.assertRaises(Rejected):
            static_top(.2, [0, 0, 0], [0, 0, -9.81], [0, 0, .981], [0, 0, .981], [0, 0, 0])

    def test_wrong_normal_direction_and_double_count_are_rejected(self):
        for force in ([0, 0, -.981], [0, 0, 1.962]):
            with self.assertRaises(Rejected):
                static_top(.1, [0, 0, 0], [0, 0, -9.81], list(force), list(force), [0, 0, 0])

    def test_reciprocal_components_separately_not_cancelled_combined(self):
        reciprocal([0, 0, .981], [0, 0, -.981], [0, 0, 0], [0, 0, 0])
        # Combined sums cancel, but each kind fails independently.
        with self.assertRaisesRegex(Rejected, "reciprocal normal"):
            reciprocal([0, 0, .981], [0, 0, -.881], [0, 0, 0], [0, 0, -.1])

    def test_dt_values_already_converted_no_double_division(self):
        dt_consistency([[0, 0, .981/240], [0, 0, .981], [0, 0, .4905]], 1/240)
        with self.assertRaises(Rejected):
            dt_consistency([[0, 0, .981/240], [0, 0, .981*240], [0, 0, .4905*240]], 1/240)
        with self.assertRaises(Rejected):
            dt_consistency([[0, 0, .981/240], [0, 0, .981], [0, 0, .981]], 1/240)

    def test_nonfinite_bool_and_nonunit_normal_reject(self):
        for bad in (math.nan, math.inf, True):
            with self.assertRaises(Rejected):
                signed_pair_sum([{"scalar": bad, "normal": [0, 0, 1]}])
        with self.assertRaises(Rejected):
            signed_pair_sum([{"scalar": .981, "normal": [0, 0, 2]}])

    def test_all_low_motion_dimensions_and_zero_friction(self):
        low_motion([0, 0, 0], [0, 0, 0], [0, 0, 0], [0, 0, 0])
        for position, value in enumerate((.006, .03, .06, .11)):
            vectors = [[0, 0, 0] for _ in range(4)]
            vectors[position][0] = value
            with self.assertRaises(Rejected):
                low_motion(*vectors)
        with self.assertRaises(Rejected):
            static_top(.1, [0, 0, 0], [0, 0, -9.81], [0, 0, .981], [0, 0, .981], [.001, 0, 0])


if __name__ == "__main__":
    unittest.main()
