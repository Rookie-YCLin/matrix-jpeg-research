"""Unit tests for strict zero-BER-first selection."""
import unittest

from experiments.adaptive_d1_zero_ber_selection import select


def row(d1, worst, psnr, clean=0):
    return {"d1": d1, "worst_ber": worst,
            "png_psnr_db": psnr, "clean_errors": clean}


class ZeroBerSelectionTests(unittest.TestCase):
    def test_psnr_wins_only_among_zero_ber_candidates(self):
        result = select([row(36, .25, 42), row(90, 0, 35),
                         row(140, 0, 29), row(720, 0, 15)])
        self.assertEqual(result["best_zero_ber_d1"], 90)
        self.assertEqual(result["status"], "feasible")

    def test_no_zero_ber_reports_infeasible(self):
        result = select([row(10, .1, 40), row(20, .02, 32)])
        self.assertEqual(result["status"], "infeasible_in_measured_domain")
        self.assertIsNone(result["best_zero_ber_d1"])

    def test_clean_bit_errors_are_not_feasible(self):
        result = select([row(40, 0, 39, 1), row(60, 0, 35, 0)])
        self.assertEqual(result["best_zero_ber_d1"], 60)

    def test_optional_quality_floor(self):
        result = select([row(90, 0, 35), row(120, 0, 31)], psnr_floor=36)
        self.assertEqual(result["status"], "infeasible_in_measured_domain")

    def test_ties_and_duplicates(self):
        self.assertEqual(select([row(50, 0, 30), row(40, 0, 30)])["best_zero_ber_d1"], 40)
        with self.assertRaises(ValueError):
            select([row(40, 0, 30), row(40, 0, 30)])


if __name__ == "__main__":
    unittest.main()
