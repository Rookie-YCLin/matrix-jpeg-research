from experiments.adaptive_d1_grid import Evaluation, parse_d1_values, summarise


def test_parse_d1_values_is_positive_unique_and_inclusive():
    assert parse_d1_values("3:5") == (3, 4, 5)
    assert parse_d1_values("5,1,5") == (1, 5)


def test_summary_requires_all_qfs_and_computes_models():
    rows = [
        Evaluation(7, qf, 0, 32, 0.0, "0" * 32, 41.0, 5.0, 0.1, 0.2, 0)
        for qf in (5, 6, 7, 8, 9, 10)
    ]
    result = summarise(rows)
    assert result[0]["model_a_feasible"] is True
    assert result[0]["model_b_lambda_0_5"] == 0.0
