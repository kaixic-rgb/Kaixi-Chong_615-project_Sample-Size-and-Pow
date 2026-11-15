import math

import numpy as np
from scipy.stats import nct, t


MAX_N = 1_000_000


class PowerError(ValueError):
    pass


def finite_number(value, name):
    if isinstance(value, (bool, np.bool_)):
        raise PowerError(f"{name} must be a finite number.")
    try:
        number = float(value)
    except (TypeError, ValueError, OverflowError):
        raise PowerError(f"{name} must be a finite number.") from None
    if not math.isfinite(number):
        raise PowerError(f"{name} must be a finite number.")
    return number


def check_alpha(alpha):
    alpha = finite_number(alpha, "Significance level")
    if not 0 < alpha < 1:
        raise PowerError("Significance level must be between 0 and 1 (not including the endpoints).")
    if alpha / 2 == 0:
        raise PowerError("Significance level is too small for reliable floating-point calculations.")
    return alpha


def check_effect(d):
    return abs(finite_number(d, "Cohen's d"))


def effect_from_means(mean_difference, sd):
    difference = finite_number(mean_difference, "Mean difference")
    sd = finite_number(sd, "Standard deviation")
    if sd <= 0:
        raise PowerError("Standard deviation must be greater than zero.")
    d = abs(difference) / sd
    if not math.isfinite(d):
        raise PowerError("The standardized effect size is too large to calculate reliably.")
    if difference != 0 and d == 0:
        raise PowerError("The standardized effect size is too small to represent reliably.")
    return d


def check_n(n):
    if isinstance(n, (bool, np.bool_)) or not isinstance(n, (int, np.integer)):
        raise PowerError("Sample size per group must be an integer.")
    if not 2 <= n <= MAX_N:
        raise PowerError(f"Sample size per group must be between 2 and {MAX_N:,}.")
    return int(n)


def calculate_power(n, d, alpha=0.05):
    n = check_n(n)
    d = check_effect(d)
    alpha = check_alpha(alpha)

    df = 2 * n - 2
    crit = float(t.isf(alpha / 2, df))
    ncp = d * math.sqrt(n / 2)
    if not math.isfinite(crit) or not math.isfinite(ncp):
        raise PowerError("This combination of inputs is outside the reliable numerical range.")

    if d == 0:
        return alpha

    upper = float(nct.sf(crit, df, ncp))
    lower = float(nct.cdf(-crit, df, ncp))
    if not math.isfinite(lower):
        lower = float(nct.sf(crit, df, -ncp))
    tolerance = 32 * np.finfo(float).eps
    if not all(math.isfinite(x) for x in (upper, lower)):
        raise PowerError("The probability calculation did not return a finite result.")
    if any(x < -tolerance or x > 1 + tolerance for x in (upper, lower)):
        raise PowerError("The probability calculation returned a value outside [0, 1].")

    power = math.fsum((upper, lower))
    if power < -tolerance or power > 1 + tolerance:
        raise PowerError("The calculated power is outside [0, 1].")
    return min(1.0, max(0.0, power))


def find_sample_size(d, alpha=0.05, target_power=0.80):
    d = check_effect(d)
    alpha = check_alpha(alpha)
    target = finite_number(target_power, "Target power")
    if not alpha < target < 1:
        raise PowerError("Target power must be greater than the significance level and less than 1.")
    if d == 0:
        raise PowerError("A zero effect size cannot reach a target power greater than alpha.")

    first_power = calculate_power(2, d, alpha)
    if first_power >= target:
        return 2, first_power

    low = 2
    high = 4
    while True:
        p_high = calculate_power(high, d, alpha)
        if p_high >= target:
            break
        if high == MAX_N:
            raise PowerError(f"Target power is not attainable within {MAX_N:,} participants per group.")
        low = high
        high = min(MAX_N, high * 2)

    while low + 1 < high:
        mid = (low + high) // 2
        if calculate_power(mid, d, alpha) >= target:
            high = mid
        else:
            low = mid

    achieved = calculate_power(high, d, alpha)
    previous = calculate_power(high - 1, d, alpha)
    if not achieved >= target or not previous < target:
        raise PowerError("The minimum sample size could not be verified numerically.")
    return high, achieved


def power_curve(n, d, alpha=0.05, max_points=200):
    n = check_n(n)
    d = check_effect(d)
    alpha = check_alpha(alpha)
    if not isinstance(max_points, int) or not 4 <= max_points <= 200:
        raise PowerError("The plot must use between 4 and 200 points.")

    end = min(MAX_N, max(30, math.ceil(n * 1.8)))
    count = min(max_points - 1, end - 1)
    grid = np.rint(np.linspace(2, end, count)).astype(int)
    sizes = sorted(set(grid.tolist()) | {n})
    return [{"n": size, "power": calculate_power(size, d, alpha)} for size in sizes]


def effect_sensitivity_curve(n, d, alpha=0.05, max_points=81):
    """Show power under alternative assumed effect sizes at a fixed n."""
    n = check_n(n)
    d = check_effect(d)
    alpha = check_alpha(alpha)
    if not isinstance(max_points, int) or not 5 <= max_points <= 100:
        raise PowerError("The sensitivity plot must use between 5 and 100 points.")
    if d > 10:
        raise PowerError("Effect-size sensitivity is displayed only for Cohen's d up to 10.")

    upper = max(0.75, 1.6 * d)
    values = np.linspace(0, upper, max_points - 1).tolist()
    values.append(d)
    sizes = sorted(set(float(value) for value in values))
    return [{"effect": value, "power": calculate_power(n, value, alpha)} for value in sizes]
