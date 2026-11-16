import unittest

from filament_weights import calculate_spool_weights


class CalculateSpoolWeightsTests(unittest.TestCase):
    def test_weight_below_full_spool_threshold_is_remaining_weight(self):
        weights = calculate_spool_weights(250)

        self.assertEqual(weights.used_weight_g, 750)
        self.assertEqual(weights.total_weight_g, 1000)
        self.assertEqual(weights.remaining_weight_g, 250)

    def test_full_spool_weight_is_also_remaining_weight(self):
        weights = calculate_spool_weights(1000)

        self.assertEqual(weights.used_weight_g, 0)
        self.assertEqual(weights.total_weight_g, 1000)
        self.assertEqual(weights.remaining_weight_g, 1000)

    def test_full_spool_weight_above_threshold_is_preserved(self):
        weights = calculate_spool_weights(1200)

        self.assertEqual(weights.used_weight_g, 0)
        self.assertEqual(weights.total_weight_g, 1200)
        self.assertEqual(weights.remaining_weight_g, 1200)


if __name__ == "__main__":
    unittest.main()
