"""Small reproducible demonstration of the checkpoint calculations."""

from power_calc import calculate_power, find_sample_size


def main():
    n, achieved = find_sample_size(0.5, 0.05, 0.80)
    print(f"Minimum sample size per group: {n}")
    print(f"Total sample size: {2 * n}")
    print(f"Power at n={n - 1}: {calculate_power(n - 1, 0.5, 0.05):.8f}")
    print(f"Achieved power: {achieved:.8f}")
    print("Effect-size sensitivity at fixed n and alpha:")
    for effect in (0.3, 0.5, 0.8):
        print(f"  Cohen's d={effect:.1f}: power={calculate_power(n, effect, 0.05):.6f}")


if __name__ == "__main__":
    main()
