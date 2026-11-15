import importlib.util
from pathlib import Path

import numpy as np
import pytest
from statsmodels.stats.power import TTestIndPower

from power_calc import (
    MAX_N,
    PowerError,
    calculate_power,
    check_n,
    effect_from_means,
    effect_sensitivity_curve,
    find_sample_size,
    power_curve,
)


@pytest.mark.parametrize(
    "n,alpha,d",
    [
        (2, 0.05, 0.5),
        (10, 0.01, 0.2),
        (30, 0.05, 0.8),
        (64, 0.05, 0.5),
        (100, 0.1, 1.0),
        (1000, 0.01, 0.1),
    ],
)
def test_matches_statsmodels(n, alpha, d):
    expected = TTestIndPower().power(effect_size=d, nobs1=n, alpha=alpha, ratio=1, alternative="two-sided")
    assert calculate_power(n, d, alpha) == pytest.approx(expected, abs=1e-6)


def test_default_example():
    n, achieved = find_sample_size(0.5, 0.05, 0.80)
    assert n == 64
    assert achieved == pytest.approx(0.8014595579222543, abs=1e-9)
    assert calculate_power(63, 0.5, 0.05) < 0.80


@pytest.mark.parametrize(
    "d,alpha,target",
    [(0.2, 0.05, 0.8), (0.5, 0.05, 0.9), (1.2, 0.01, 0.95), (10, 0.05, 0.8)],
)
def test_minimum_integer_n(d, alpha, target):
    n, achieved = find_sample_size(d, alpha, target)
    assert 2 <= n <= MAX_N
    assert achieved >= target
    assert n == 2 or calculate_power(n - 1, d, alpha) < target


def test_equal_tails_zero_effect():
    for alpha in (0.001, 0.05, 0.2):
        for n in (2, 50, MAX_N):
            assert calculate_power(n, 0, alpha) == alpha


def test_power_rises_with_n_and_effect():
    by_n = [calculate_power(n, 0.3, 0.05) for n in (2, 5, 10, 30, 100, 500)]
    by_effect = [calculate_power(50, d, 0.05) for d in (0, 0.1, 0.3, 0.5, 1)]
    assert all(0 <= p <= 1 for p in by_n + by_effect)
    assert all(b >= a - 1e-12 for a, b in zip(by_n, by_n[1:]))
    assert all(b >= a - 1e-12 for a, b in zip(by_effect, by_effect[1:]))


def test_effect_input_signs():
    assert effect_from_means(-2, 4) == 0.5
    assert effect_from_means(2, 4) == 0.5
    assert calculate_power(64, -0.5) == calculate_power(64, 0.5)


@pytest.mark.parametrize("alpha", [0, 1, -0.1, float("nan"), float("inf"), 5e-324])
def test_bad_alpha(alpha):
    with pytest.raises(PowerError):
        calculate_power(64, 0.5, alpha)


@pytest.mark.parametrize("target", [0, 0.05, 1, 1.1, float("nan"), float("inf")])
def test_bad_target(target):
    with pytest.raises(PowerError):
        find_sample_size(0.5, 0.05, target)


@pytest.mark.parametrize("sd", [0, -1, float("nan"), float("inf")])
def test_bad_sd(sd):
    with pytest.raises(PowerError):
        effect_from_means(0.5, sd)


@pytest.mark.parametrize("n", [0, 1, MAX_N + 1, 64.0, 12.4, "64", True])
def test_bad_sample_size(n):
    with pytest.raises(PowerError):
        check_n(n)


@pytest.mark.parametrize("d", [float("nan"), float("inf"), -float("inf"), "not a number"])
def test_bad_effect_size(d):
    with pytest.raises(PowerError):
        calculate_power(64, d)


def test_zero_effect_does_not_solve_for_n():
    with pytest.raises(PowerError, match="zero effect"):
        find_sample_size(0, 0.05, 0.8)


def test_unattainable_within_limit():
    with pytest.raises(PowerError, match="not attainable"):
        find_sample_size(1e-6, 0.05, 0.8)


def test_numeric_extremes():
    with pytest.raises(PowerError, match="too large"):
        effect_from_means(1e308, 1e-308)
    with pytest.raises(PowerError, match="too small"):
        effect_from_means(1e-308, 1e308)
    with pytest.raises(PowerError, match="numerical range"):
        calculate_power(MAX_N, 1e308)
    assert 0 <= calculate_power(MAX_N, 0.5) <= 1
    assert 0 <= calculate_power(64, 0.5, 1e-12) <= 1


def test_tiny_effect_close_to_alpha():
    assert calculate_power(100, 1e-150) == pytest.approx(0.05, abs=1e-12)


def test_small_lower_tail_stays_finite():
    assert 0 <= calculate_power(911, 0.5) <= 1


def test_plot_is_bounded_and_includes_chosen_n():
    for n in (2, 64, 100_003, MAX_N):
        points = power_curve(n, 0.5)
        sizes = [point["n"] for point in points]
        assert len(points) <= 200
        assert sizes == sorted(set(sizes))
        assert n in sizes
        assert all(2 <= x <= MAX_N for x in sizes)
        assert all(0 <= point["power"] <= 1 for point in points)


def test_invalid_plot_budget():
    with pytest.raises(PowerError):
        power_curve(64, 0.5, max_points=1000)


def test_app_imports_without_running_ui():
    path = Path(__file__).resolve().parents[1] / "app.py"
    spec = importlib.util.spec_from_file_location("sample_size_app_smoke", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    assert callable(module.main)


def test_effect_sensitivity_includes_assumed_effect():
    n = 64
    d = 0.5
    points = effect_sensitivity_curve(n, d, 0.05)
    assert len(points) <= 81
    assert [p["effect"] for p in points] == sorted({p["effect"] for p in points})
    selected = next(p for p in points if p["effect"] == d)
    assert selected["power"] == pytest.approx(calculate_power(n, d, 0.05))
    assert points[0]["effect"] == 0
    assert points[0]["power"] == pytest.approx(0.05)


def test_sensitivity_is_monotone_in_effect():
    points = effect_sensitivity_curve(64, 0.5)
    powers = [p["power"] for p in points]
    assert all(b >= a - 1e-12 for a, b in zip(powers, powers[1:]))


def test_sensitivity_limits():
    with pytest.raises(PowerError):
        effect_sensitivity_curve(64, 11)
    with pytest.raises(PowerError):
        effect_sensitivity_curve(64, 0.5, max_points=1001)
