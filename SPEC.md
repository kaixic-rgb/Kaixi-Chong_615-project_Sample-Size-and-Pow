# Sample Size and Power Calculator

## 1. Project overview

Build a small interactive web app for sample size and statistical power calculations. This is a Track A project for BIOSTAT 615, a graduate statistical computing course. The app is aimed at students and researchers planning a study with a continuous outcome and two independent groups.

The first version supports one statistical design: an independent, two-sided, pooled-variance two-sample t-test with equal group sizes (1:1 allocation). It should be easy to use, but the statistical calculations should be implemented and tested carefully. Do not add other tests or study designs to the first version.

Use **Python 3.12, Streamlit, SciPy, NumPy, and Altair**. Host the finished app on Streamlit Community Cloud using a GitHub repository. Keep the calculation code separate from the interface. No database, sign-in, or patient-level data is needed.

## 2. Requirements and design choices

The first version should follow these requirements:

1. Independent two-sample, two-sided t-test; equal variances; 1:1 allocation; calculate power using the noncentral t distribution.
2. Two effect-size input modes: mean difference plus common standard deviation (default), and Cohen's d. Validate inputs.
3. Two calculation modes: Calculate Sample Size and Calculate Power. Return the smallest valid integer sample size and recompute achieved power.
4. One interactive Power vs. Sample Size plot with the target power and selected sample size highlighted. Limit the amount of plotting work.
5. Use numerically stable SciPy probability functions. Handle cancellation, underflow, overflow, nonfinite values, and extreme inputs explicitly.
6. Find sample size using exponential upper-bound expansion and integer binary search. Allow 2 through 1,000,000 participants per group; verify the result at n and n-1.
7. Test with pytest, comparisons against statsmodels, mathematical properties, extreme numerical cases, and GitHub Actions.
8. Python 3.12, Streamlit, SciPy/NumPy, Altair; separate calculations and UI; deploy with GitHub and Streamlit Community Cloud; no database or user accounts.
9. Single-page layout, dynamic inputs and results, interactive plot, clear validation and errors, assumptions explained, and no automatic dropout adjustment.

## 3. Statistical definitions and assumptions

Let n be the number of participants **per group** and N = 2n the total sample size. Let Delta be the difference between the two population means, sigma > 0 the common standard deviation, and d = abs(Delta)/sigma the absolute standardized effect size. For Cohen's d input, use its absolute value for the two-sided power calculation.

For a two-sided significance level alpha:

- Degrees of freedom: `df = 2*n - 2`.
- Noncentrality parameter: `ncp = d * sqrt(n / 2)`.
- Upper critical value: `crit = scipy.stats.t.isf(alpha / 2, df)`.
- Power: `scipy.stats.nct.sf(crit, df, ncp) + scipy.stats.nct.cdf(-crit, df, ncp)`.

This is the probability of rejecting the null hypothesis under the assumed nonzero effect, summing both rejection tails. Do **not** calculate the upper tail as `1 - cdf(crit)`, which can suffer catastrophic cancellation. For moderate ordinary inputs, verify this calculation against `statsmodels.stats.power.TTestIndPower.power(effect_size=d, nobs1=n, alpha=alpha, ratio=1, alternative="two-sided")`.

At `d = 0`, the population-level power equals alpha. This is allowed in Calculate Power mode, but Calculate Sample Size must not attempt to find a finite n for a target power larger than alpha when d = 0.

Assumptions shown in the UI: independent observations, continuous outcome, common within-group variance, two-sided pooled two-sample t-test, and equal allocation. The app does not model attrition or adjust sample size for dropout.

## 4. Calculation modes

### Calculate Sample Size

Inputs:

- Effect size: either (mean difference, common SD) or Cohen's d.
- Significance level alpha (default 0.05).
- Target power (default 0.80).

Outputs:

- Smallest integer n per group, with `2 <= n <= 1_000_000`, whose computed power reaches the target.
- Total participants `2*n`.
- Recomputed achieved power at this integer n.
- Beta = 1 - achieved power (format carefully near zero).
- Power curve with a target-power line and the chosen n marked.

Do not round an approximate continuous sample-size result and assume it is minimal. Use the actual noncentral t power function for the integer search and confirm minimality.

### Calculate Power

Inputs:

- Effect size in either input mode.
- Alpha (default 0.05).
- Integer n per group (default 64).

Outputs:

- Calculated power and beta.
- n per group and total N.
- Power curve, with the supplied n and calculated power marked.

The plot may display a target power line when there is a target; in Calculate Power mode it should not imply that a target was supplied. If useful, mark only the entered sample size and its power.

## 5. Minimum integer sample size algorithm

Use this search order:

1. Validate inputs; compute d safely and make sure it is finite.
2. Evaluate the power at n = 2. If it already meets the target, return 2.
3. Starting above n = 2, repeatedly double the candidate upper bound (without exceeding 1,000,000) until computed power reaches the target or the cap is reached. Maintain a lower bound known not to reach the target.
4. If even n = 1,000,000 does not reach the target, show a clear "not attainable within the supported range" message; do not pretend a solution exists.
5. Perform integer binary search between the failing lower bound and the successful upper bound.
6. Re-evaluate power at the candidate n and, if n > 2, at n-1. Require `power(n) >= target` and `power(n-1) < target`. If the numeric results are unreliable, report a calculation issue rather than returning an unverified n.

The search should need only O(log Nmax) power evaluations; avoid scanning every sample size.

## 6. Input validation and numerical stability

Validation happens before numerical computation. For invalid inputs, show a short, specific message and do not display stale results from an earlier calculation.

- Alpha must be finite and strictly between 0 and 1.
- Target power must be finite, greater than alpha, and strictly below 1 for Calculate Sample Size.
- SD must be finite and strictly positive.
- Mean difference and Cohen's d must be finite. Negative values are allowed but treated by absolute magnitude in this two-sided test.
- n must be an integer between 2 and 1,000,000 per group.
- A zero effect size is allowed only in Calculate Power mode; a target strictly above alpha is unattainable with zero effect.
- After calculating `d = abs(Delta)/sigma`, require a finite result; guard against overflow even if Delta and sigma were individually finite.
- Reject or explain calculations whose `crit`, `ncp`, or probability outputs are nonfinite or outside a valid probability range beyond harmless floating-point rounding.
- Do not blindly clamp large numerical errors to [0, 1]. Small roundoff (on the order of machine precision) can be corrected only with a documented tolerance in the implementation.
- For very small alpha, use `t.isf(alpha/2, df)` rather than `t.ppf(1-alpha/2, df)`. If `alpha/2` underflows to zero or SciPy cannot return a trustworthy finite critical value, explain that the input is outside the reliable numeric range.
- Do not promise arbitrary precision for extreme inputs. When exact reliability cannot be established, show an informative error or limitation.
- Use log-domain methods, `log1p`, or `expm1` only when an actual operation requires them; do not add unnecessary transforms to SciPy's stable tail functions.
- Avoid displaying small nonzero probabilities as exact zero just because of aggressive rounding; show scientific notation when appropriate.

Provide clear messages for impossible target power, values outside the supported sample-size range, nonfinite outputs, and invalid numeric inputs.

## 7. Single-page Streamlit interface

At the top, describe the test and its assumptions in a short paragraph. Use the following order:

1. Select Calculate Sample Size or Calculate Power.
2. Select Mean Difference + SD (default) or Cohen's d.
3. Enter the fields needed for the selected mode; hide irrelevant inputs.
4. Display the appropriate results and a Power vs. Sample Size chart.
5. Show assumptions, limits, and a brief explanation of what the results mean.

Valid input changes should refresh the relevant results and plot. Streamlit may rerun the page, but statistical work should remain bounded. The graph uses n per group on the x-axis and power on the y-axis, includes hover values, and highlights the meaningful sample size and power. In Sample Size mode, draw a horizontal target-power line. Compute at most about 200 plotting points; include the exact reported n even if it is not in the regular grid. Do not allocate arrays with one million plotting points.

Default example: alpha = 0.05, d = 0.5, target power = 0.80. This requires n = 64 per group, total N = 128, achieved power approximately 0.80145956. These numbers are test fixtures, not hardcoded results.

## 8. Software structure

Suggested repository files:

```text
app.py
power_calc.py
requirements.txt
requirements-dev.txt
README.md
SPEC.md
tests/test_power_calc.py
.github/workflows/tests.yml
```

- `power_calc.py`: pure Python functions for validation, effect size conversion, noncentral t power, integer search, and plot-point generation. These functions should not import Streamlit.
- `app.py`: interface, input widgets, results, chart, and user-friendly errors. Avoid statistical formulas duplicated in the UI code.
- `requirements.txt`: compatible, pinned runtime dependencies. Include Streamlit, SciPy, NumPy, and Altair; include Pandas only if the chart implementation needs it.
- `requirements-dev.txt`: pytest and statsmodels, plus runtime dependencies for CI. Statsmodels is a verification reference, not the app's runtime calculation engine.
- `README.md`: project purpose, assumptions, requirements, local setup and run command (`streamlit run app.py`), tests, and hosted app URL after deployment.
- `.github/workflows/tests.yml`: run pytest for pushes and pull requests using Python 3.12.

Prefer straightforward, student-like naming and readable functions. Avoid adding unnecessary source-code comments or elaborate abstractions. Existing comments in any starter files should be preserved if the implementation later uses them.

## 9. Testing plan

Use `pytest` for the following categories:

1. **Reference comparisons:** compare power for several ordinary combinations of n, alpha, and d with statsmodels `TTestIndPower`. For well-behaved cases, use absolute tolerance <= 1e-6. Do not assume statsmodels is independent of SciPy internally; use other checks too.
2. **Mathematical properties:** power stays in [0,1]; for d >= 0 power should not decrease materially as n increases or as d increases; d = 0 returns approximately alpha; changing the sign of the entered mean difference does not change two-sided power.
3. **Minimum n:** at each returned n, check `power(n) >= target` and either `n == 2` or `power(n-1) < target`. Check several standard and difficult examples, including cases where the solution is at a search boundary.
4. **Input errors:** alpha 0/1, target outside (alpha,1), SD 0/negative, noninteger n, n below 2 or above 1,000,000, nonfinite inputs, and zero effect in Sample Size mode.
5. **Numerical limits:** very small alpha, tiny and very large effects, targets near 1, overflow in effect-size conversion, very large n, and an unattainable target before the n cap. Assert clean errors when precision is unreliable.
6. **Interface smoke check:** ensure the Streamlit entrypoint imports and that core calculation functions remain usable without the web UI.

CI should run automatically on push and pull request. Avoid tests that depend on live internet access or tight timing thresholds. Under ordinary inputs the app should feel responsive; plot sampling must remain bounded.

## 10. Project boundaries and acceptance criteria

Required first-version features: both modes, both effect-size formats, correct noncentral-t calculations, minimal integer n, achieved-power recomputation, one interactive plot, clear validation, numerical guardrails, automated tests, working deployment, and basic documentation.

Out of scope for v1: Welch's t-test, paired tests, ANOVA, one-sided alternatives, unequal group allocations, attrition/dropout adjustment, clinical data upload, persistent database, logins, and external APIs.

Treat the project as ready when:

- Statistical outputs match reference values in ordinary cases, including the default d = 0.5 example.
- Returned sample sizes pass both n and n-1 checks.
- Extreme/invalid inputs are either handled correctly or rejected clearly without crashing.
- The UI shows the right fields, correct output labels, and an interactive bounded-size chart.
- The automated tests pass locally and through GitHub Actions.
- The app starts with `streamlit run app.py`, deploys successfully to Streamlit Community Cloud, and has a usable URL.
- A README and dependency files allow another person to reproduce the calculation environment.

## 11. Suggested implementation order

1. Set up repository, Python version, dependencies, and basic tests.
2. Write the effect-size validation and the pure noncentral-t power function.
3. Cross-check several values with statsmodels and add tests for numerical boundaries.
4. Add the expanding upper bound and binary search; test minimality and no-solution cases.
5. Build the Streamlit form, results, assumptions, and dynamic plot.
6. Add end-to-end smoke checks, documentation, GitHub Actions, and Streamlit Community Cloud deployment.

## 12. Milestones and November 23 checkpoint

The project should be developed in stages so that there is a working application by the November 23 checkpoint. The dates below are planning targets, not additional features.

- **By October 26:** Finalize this specification, create the GitHub repository, and submit the project proposal.
- **By November 9:** Implement the noncentral-t power calculation and the minimum-integer sample-size search. Add basic validation and reference tests against statsmodels.
- **By November 16:** Build the first Streamlit interface with both calculation modes, both effect-size input methods, and the interactive Power vs. Sample Size curve.
- **By November 23 (checkpoint):** Have a working version in the GitHub repository. It should run locally, calculate sample size and power using the agreed assumptions, validate common invalid inputs, show the power curve, and pass the main automated tests. The default example must return 64 participants per group with power close to 0.80146.
- **After the checkpoint:** Improve the handling of numerical edge cases, finish the full test suite and GitHub Actions checks, polish instructions and labels, and deploy the app to Streamlit Community Cloud before the final project deadline.

If time is limited before November 23, prioritize correct calculations, both modes, and a usable interface. Do not add more statistical tests until the required features work.

## 13. Risks and how to handle them

- **Numerical instability:** Extremely small probabilities or large effects may cause underflow, overflow, or unreliable SciPy results. Use stable tail probabilities, validate intermediate values, test difficult cases, and show an error when a result cannot be trusted.
- **Sample-size limit:** A very small effect or high target power may require more than 1,000,000 people per group. Report that the target cannot be reached within the supported range instead of returning a misleading number.
- **Statistical assumptions:** Researchers may try to use the calculator for unequal variances, unequal allocation, or paired data. State the assumptions clearly and keep unsupported designs out of the first version.
- **Time and scope:** Extra statistical tests or plots could delay the working app. Finish and verify the agreed first-version features before considering additions.
- **Deployment and dependencies:** Package versions or Streamlit Community Cloud settings might cause the hosted app to behave differently from the local version. Pin dependencies, keep setup instructions, run tests in GitHub Actions, and check the deployed app with the default example.

Do not start implementing code until the user approves the final design and requests implementation. This specification is the planning deliverable.
