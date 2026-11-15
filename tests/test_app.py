from pathlib import Path

from streamlit.testing.v1 import AppTest


APP = str(Path(__file__).resolve().parents[1] / "app.py")


def test_default_page():
    app = AppTest.from_file(APP).run(timeout=30)
    assert not app.exception
    assert app.metric[0].value == "64"
    assert app.metric[1].value == "128"
    assert app.get("arrow_vega_lite_chart")


def test_calculate_power_mode():
    app = AppTest.from_file(APP).run(timeout=30)
    app.radio[0].set_value("Calculate Power").run(timeout=30)
    assert not app.exception
    assert app.metric[0].value == "64"
    assert app.metric[1].value == "128"
    assert app.get("arrow_vega_lite_chart")


def test_cohens_d_mode():
    app = AppTest.from_file(APP).run(timeout=30)
    app.radio[1].set_value("Cohen's d").run(timeout=30)
    assert not app.exception
    assert app.metric[0].value == "64"


def test_bad_sd_shows_error_without_old_results():
    app = AppTest.from_file(APP).run(timeout=30)
    app.number_input[1].set_value(0.0).run(timeout=30)
    assert app.error
    assert not app.metric


def test_checkpoint_sensitivity_expander():
    app = AppTest.from_file(APP).run(timeout=30)
    assert not app.exception
    assert any("Effect-size sensitivity" in item.label for item in app.expander)
