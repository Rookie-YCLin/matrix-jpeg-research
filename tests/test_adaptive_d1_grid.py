from experiments.adaptive_d1_grid import Evaluation, parse_d1_values, summarise


def test_parse_d1_values_is_positive_unique_and_inclusive():
    assert parse_d1_values("3:5") == (3, 4, 5)
    assert parse_d1_values("5,1,5") == (1, 5)


def test_summary_requires_all_qfs_and_computes_models():
    rows = [
        Evaluation(
            d1=7, qf=qf, errors=0, total_bits=32, ber=0.0,
            extracted_bits="0" * 32, png_psnr_db=41.0,
            png_mse_rgb_8bit=5.0, clean_errors=0,
            embed_seconds=0.1, jpeg_extract_seconds=0.2,
        )
        for qf in (5, 6, 7, 8, 9, 10)
    ]
    result = summarise(rows)
    assert result[0]["model_a_feasible"] is True
    assert result[0]["model_b_lambda_0_5"] == 0.0
