# Sample Size & Power Calculator

A single-page Streamlit tool for sample size and power in an independent, two-sided, pooled-variance two-sample t-test. Built for the University of Michigan BIOSTAT 615 final project (Track A).

## Features

- Find the smallest integer sample size per group for a requested target power.
- Calculate power from a sample size per group.
- Enter an expected difference in means plus a common standard deviation, or Cohen's d.
- Explore an interactive power-versus-sample-size plot.
- Get clear input errors and explanations of the statistical assumptions.

The calculations use the noncentral t distribution, equal allocation (1:1), a common variance, and a two-sided alternative. Sample-size results are checked at both the selected n and n-1. There is no dropout adjustment.

## Run locally

Use Python 3.12. In this project directory:

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
streamlit run app.py
```

On Windows, activate the environment with `.venv\Scripts\activate` instead.

Streamlit shows the local address in the terminal (usually `http://localhost:8501`).

## Tests

```bash
python -m pip install -r requirements-dev.txt
python -m pytest -q
```

The tests compare ordinary power values against statsmodels, verify sample-size minimality, exercise invalid and extreme numerical inputs, and check that plots stay small. GitHub Actions runs them on pushes and pull requests.

## Example

With a two-sided alpha of 0.05, Cohen's d of 0.5, and target power of 0.80, the smallest sample size is **64 per group** (**128 total**). Achieved power is about **0.80145956**.

## Deploy on Streamlit Community Cloud

1. Create a GitHub repository and add the files in this folder at its root.
2. Push the repository to GitHub. Confirm the GitHub Actions tests pass.
3. At [Streamlit Community Cloud](https://share.streamlit.io/), select **Create app** and choose this GitHub repository.
4. Set the main file path to `app.py`, deploy, and check both calculation modes.
5. Add the new app's URL to this README and to the course submission if needed.

**Hosted app:** Not deployed yet (requires the project owner's GitHub and Streamlit Cloud account).

## Scope

This is a planning tool, not a substitute for statistical design consultation. It does not support unequal allocation, Welch's t-test, paired designs, one-sided tests, missing-data adjustments, or participant-level data. Sample sizes are limited to 2–1,000,000 participants per group; inputs outside the reliable floating-point range raise an error.

## November 23 checkpoint

A checkpoint progress report with verified examples, current limitations, and a demonstration plan is available in [`CHECKPOINT.md`](CHECKPOINT.md). The implementation also includes an optional **effect-size sensitivity plot**. At a fixed sample size, the extra plot illustrates how power changes when the assumed effect size changes. This does not change the underlying two-sample t-test model.

For a quick calculation-only check (no web server required):

```bash
python checkpoint_demo.py
```
