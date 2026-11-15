# BIOSTAT 615 Final Project — Checkpoint progress

**Project:** Sample Size & Power Calculator for Two Independent Groups  
**Track:** A (Streamlit web app)  
**Repository:** https://github.com/kaixic-rgb/Kaixi-Chong_615-project_Sample-Size-and-Pow  
**Checkpoint target:** November 23, 2026

## What is implemented

I have working Python functions for a two-sided independent two-sample t-test with equal variance and 1:1 allocation. The app calculates either the smallest sample size meeting a target power or the power for an entered sample size. Users can enter a mean difference and common standard deviation, or Cohen's d.

I use the noncentral t distribution for power. For sample size, I first find a working upper bound and then use integer binary search. I check both n and n - 1 so that the answer is the smallest supported integer sample size. The Streamlit page includes the inputs, results, a Power vs. Sample Size plot, validation messages, and the main assumptions.

**New for the checkpoint:** I added an optional effect-size sensitivity plot. At the selected sample size, it shows how power changes if the real effect size is different from the original assumption. This is useful because the expected effect size is usually uncertain when planning a study.

## Example results

Default case: two-sided alpha = 0.05, Cohen's d = 0.5, target power = 0.80.

| Output | Result |
| --- | ---: |
| Minimum sample size per group | 64 |
| Total sample size | 128 |
| Achieved power | 0.80145956 |
| Power at n = 63 per group | 0.79516834 |

The n = 63 result is below the target, while n = 64 reaches it.

In the effect-size sensitivity analysis, holding n = 64 and alpha = 0.05 fixed:

| Assumed Cohen's d | Power |
| ---: | ---: |
| 0.3 | 0.391469 |
| 0.5 | 0.801460 |
| 0.8 | 0.994309 |

This shows why a sample-size result depends strongly on the assumed effect size.

## Testing and current status

- Comparison tests against `statsmodels` and numerical / boundary tests are included.
- On November 15, 2026, **51 independent calculation tests passed** in the available environment.
- Python syntax checks passed.
- The UI tests are included but **were not executed here** because Streamlit and Altair are not installed in this environment. After installing `requirements-dev.txt`, run the full test suite locally and in GitHub Actions.
- This package is ready to upload, but **no GitHub push, hosted deployment, or Canvas submission has been performed**.

## How to demonstrate it

1. Install Python 3.12 and run `python -m pip install -r requirements-dev.txt`.
2. Run `python -m pytest -q`.
3. Run `streamlit run app.py` and open the local URL.
4. Show Calculate Sample Size with alpha = 0.05, d = 0.5, target = 0.80 (should give 64 per group).
5. Switch to Calculate Power with n = 64, then expand "Effect-size sensitivity" to demonstrate the added plot.
6. Enter SD = 0 in Mean Difference + SD mode to demonstrate an error message.

## Next steps after the checkpoint

My priorities are to run the full Streamlit UI tests on Python 3.12, push all source files to GitHub, check the GitHub Actions run, deploy the app to Streamlit Community Cloud, and test the hosted version. I would only expand to additional statistical tests after the present two-sample version is working reliably.

**Scope:** Equal-variance independent groups, two-sided test, 1:1 allocation, and no dropout adjustment. This is a planning tool and does not cover every study design.
