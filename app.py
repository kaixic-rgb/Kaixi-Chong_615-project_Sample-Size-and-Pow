import altair as alt
import streamlit as st

from power_calc import PowerError, calculate_power, effect_from_means, find_sample_size, power_curve, effect_sensitivity_curve


def format_probability(value):
    if value == 0:
        return "0"
    if value == 1:
        return "1"
    if value < 0.000001 or 1 - value < 0.000001:
        return f"{value:.12g}"
    return f"{value:.6f}"


def make_chart(points, selected_n, selected_power, target=None):
    source = alt.Data(values=points)
    x = alt.X("n:Q", title="Participants per group", scale=alt.Scale(zero=False))
    y = alt.Y("power:Q", title="Statistical power", scale=alt.Scale(domain=[0, 1]))
    line = (
        alt.Chart(source)
        .mark_line(color="#2374b4", strokeWidth=3)
        .encode(x=x, y=y, tooltip=[alt.Tooltip("n:Q", title="n per group"), alt.Tooltip("power:Q", format=".6f")])
    )
    dot = (
        alt.Chart(alt.Data(values=[{"n": selected_n, "power": selected_power}]))
        .mark_point(filled=True, size=145, color="#e0722c")
        .encode(x=x, y=y, tooltip=[alt.Tooltip("n:Q", title="Selected n"), alt.Tooltip("power:Q", format=".8f")])
    )
    vertical = (
        alt.Chart(alt.Data(values=[{"n": selected_n}]))
        .mark_rule(color="#e0722c", strokeDash=[4, 4], opacity=0.65)
        .encode(x="n:Q")
    )
    layers = [line, vertical, dot]
    if target is not None:
        target_line = (
            alt.Chart(alt.Data(values=[{"target": target}]))
            .mark_rule(color="#388c60", strokeDash=[7, 4], strokeWidth=2)
            .encode(y="target:Q", tooltip=[alt.Tooltip("target:Q", title="Target power", format=".6f")])
        )
        layers.append(target_line)
    return alt.layer(*layers).properties(height=370).interactive()


def make_sensitivity_chart(points, effect, selected_power):
    source = alt.Data(values=points)
    x = alt.X("effect:Q", title="Assumed Cohen's d", scale=alt.Scale(zero=True))
    y = alt.Y("power:Q", title="Statistical power", scale=alt.Scale(domain=[0, 1]))
    line = (
        alt.Chart(source)
        .mark_line(color="#6b58a0", strokeWidth=3)
        .encode(x=x, y=y, tooltip=[alt.Tooltip("effect:Q", format=".3f"),
                                   alt.Tooltip("power:Q", format=".6f")])
    )
    dot = (
        alt.Chart(alt.Data(values=[{"effect": effect, "power": selected_power}]))
        .mark_point(color="#e0722c", filled=True, size=140)
        .encode(x=x, y=y)
    )
    return alt.layer(line, dot).properties(height=290).interactive()


def main():
    st.set_page_config(page_title="Sample Size & Power Calculator", layout="centered")
    st.title("Sample Size & Power Calculator")
    st.write(
        "Plan a study with two independent groups and a continuous outcome. "
        "Calculations use a two-sided, equal-variance t-test with equal group sizes."
    )

    mode = st.radio("What would you like to calculate?", ["Calculate Sample Size", "Calculate Power"])
    input_mode = st.radio("How do you want to enter the effect?", ["Mean Difference + SD", "Cohen's d"], horizontal=True)

    if input_mode == "Mean Difference + SD":
        c1, c2 = st.columns(2)
        with c1:
            diff = st.number_input("Expected mean difference", value=0.5, format="%.10g")
        with c2:
            sd = st.number_input("Common standard deviation", value=1.0, format="%.10g")
    else:
        effect = st.number_input("Cohen's d", value=0.5, format="%.10g")

    alpha = st.number_input("Significance level (alpha)", value=0.05, format="%.10g")
    if mode == "Calculate Sample Size":
        target = st.number_input("Target power", value=0.80, format="%.10g")
    else:
        n_input = st.number_input("Participants per group", min_value=2, max_value=1_000_000, value=64, step=1)

    try:
        d = effect_from_means(diff, sd) if input_mode == "Mean Difference + SD" else abs(effect)
        if mode == "Calculate Sample Size":
            n, power = find_sample_size(d, alpha, target)
        else:
            n = int(n_input)
            power = calculate_power(n, d, alpha)
        points = power_curve(n, d, alpha)
    except (PowerError, OverflowError, ValueError) as exc:
        st.error(str(exc))
        return

    st.divider()
    st.subheader("Results")
    a, b, c = st.columns(3)
    a.metric("Per group", f"{n:,}")
    b.metric("Total participants", f"{2 * n:,}")
    c.metric("Power", format_probability(power))

    beta = 1 - power
    if beta == 0:
        st.write("Type II error probability (beta): approximately 0 at floating-point precision")
    else:
        st.write(f"Type II error probability (beta): {format_probability(beta)}")
    if mode == "Calculate Sample Size":
        st.success(f"The smallest sample size meeting target power {target:g} is {n:,} per group.")
        st.write(f"Achieved power at this integer sample size: **{format_probability(power)}**")
    else:
        st.write(f"With {n:,} participants in each group, the estimated power is **{format_probability(power)}**.")

    st.subheader("Power vs. Sample Size")
    st.altair_chart(
        make_chart(points, n, power, target if mode == "Calculate Sample Size" else None),
        use_container_width=True,
    )
    st.caption("Hover to inspect a point. Drag to zoom and double-click to reset the chart.")

    with st.expander("Effect-size sensitivity (checkpoint extension)", expanded=False):
        st.write(
            "We do not know the true effect size in advance. This plot keeps the chosen "
            "sample size fixed and shows how power changes if the real effect is "
            "smaller or larger than expected."
        )
        if d > 10:
            st.info("Sensitivity plotting is limited to Cohen's d up to 10. The main calculation is unchanged.")
        else:
            sensitivity_points = effect_sensitivity_curve(n, d, alpha)
            st.altair_chart(
                make_sensitivity_chart(sensitivity_points, d, power),
                use_container_width=True,
            )
            st.caption(
                f"Orange dot: assumed d = {d:.4g}, at n = {n:,} per group. "
                "Only the assumed effect changes; alpha and sample size stay fixed."
            )

    with st.expander("Assumptions and limitations", expanded=True):
        st.markdown(
            """
            - Independent observations and two separate groups.
            - Continuous outcomes and a common within-group standard deviation.
            - Two-sided pooled-variance t-test with 1:1 allocation.
            - Sample size is **per group**; total sample size is twice that number.
            - Power uses the noncentral t distribution under the entered effect size.
            - No adjustment for dropout or missing data is included.
            - This calculator does not support unequal group sizes, Welch's test, or paired designs.
            """
        )


if __name__ == "__main__":
    main()
