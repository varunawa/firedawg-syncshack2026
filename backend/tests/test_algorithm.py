from app.core.algorithm import compute_priority


def test_compute_priority_scales_with_word_count():
    assert compute_priority("one") == 10
    assert compute_priority("two words") == 20


def test_compute_priority_is_capped():
    assert compute_priority("a " * 50) <= 100
