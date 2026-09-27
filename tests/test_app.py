"""Rauchtests der Streamlit-Oberfläche per AppTest: Standard, jedes Preset, Randgrößen, Permalink, Auswahl, Experimente auf Abruf, Exakt-Knopf mit deaktiviertem Zustand."""

import re
from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest

import lip_constants as C
from lip_presets import PRESET_KEYS

ROOT = Path(__file__).resolve().parent.parent
APP = ROOT / "app.py"


def _run(setup=None, timeout=300):
    at = AppTest.from_file(str(APP), default_timeout=timeout)
    at.run()
    assert not at.exception, [e.value for e in at.exception]
    if setup is not None:
        setup(at)
        at.run()
        assert not at.exception, [e.value for e in at.exception]
    return at


def _apply(at, p):
    for key, state_key in PRESET_KEYS.items():
        at.session_state[state_key] = p[key]


def _metric(at, label):
    return [m.value for m in at.metric if m.label == label]


def _texts(at):
    return [e.value for e in list(at.success) + list(at.warning) + list(at.info) + list(at.error)]


def _button(at, key):
    return next(b for b in at.button if b.key == key)


def test_default_renders_and_names_the_headline_numbers():
    at = _run()
    assert _metric(at, "Geöffnet") == ["6 Lager"] and _metric(at, "Gesamtkosten") == ["6 348"]      # naive Lagermenge, Kunden bestmöglich zugeordnet (Zeile 'Neuzuordnung')
    assert any("um **4,9 %** teurer" in m.value for m in at.markdown)


@pytest.mark.parametrize("name", list(C.PRESETS))
def test_every_preset_renders(name):
    at = _run(lambda a: _apply(a, C.PRESETS[name]))
    assert not at.error and _metric(at, "Gesamtkosten")


def test_extreme_sizes_render():
    for vals in ((("sites_slider", C.SITES_MIN), ("cust_slider", C.CUST_MIN), ("hz_slider", 0), ("rho_slider", 0)),
                 (("sites_slider", C.SITES_MAX), ("cust_slider", C.CUST_MAX), ("hz_slider", 100), ("rho_slider", 100)),
                 (("hz_slider", 0), ("rho_slider", 100)),
                 (("cv_slider", C.CV_MIN), ("t_slider", C.T_MIN), ("fixed_slider", C.FIXED_MAX))):
        def setup(at, vals=vals):
            for key, value in vals:
                at.session_state[key] = value
        at = _run(setup)
        assert not at.error and _metric(at, "Gesamtkosten")


def test_selection_can_be_emptied_and_shows_a_notice_then_reflects_the_choice():
    at = _run()
    at.multiselect(key="pick_multi").set_value([])
    at.run()
    assert not at.exception and any("Wählen Sie mindestens ein Lager" in t for t in _texts(at))
    at.multiselect(key="pick_multi").set_value([0])
    at.run()
    assert not at.exception and _metric(at, "Geöffnet") == ["1 Lager"]


def test_selection_resets_when_the_net_changes():
    at = _run()
    at.multiselect(key="pick_multi").set_value([0])
    at.run()
    at.sidebar.slider(key="hz_slider").set_value(100)
    at.run()
    assert not at.exception and len(at.multiselect(key="pick_multi").value) > 1


def test_permalink_settings_are_loaded_clamped_and_snapped_to_the_grid():
    at = AppTest.from_file(str(APP), default_timeout=300)
    at.query_params["sites"] = "999"
    at.query_params["hz"] = "47"
    at.query_params["rho"] = "-5"
    at.query_params["cv"] = "33"
    at.run()
    assert not at.exception
    assert at.sidebar.slider(key="sites_slider").value == C.SITES_MAX and at.sidebar.slider(key="hz_slider").value == 45
    assert at.sidebar.slider(key="rho_slider").value == 0 and at.sidebar.slider(key="cv_slider").value == 30


def test_invalid_permalink_values_fall_back_to_the_defaults():
    at = AppTest.from_file(str(APP), default_timeout=300)
    at.query_params["hz"] = "viel"
    at.query_params["seed"] = "x"
    at.run()
    assert not at.exception and at.sidebar.slider(key="hz_slider").value == C.DEFAULT_HZ and at.sidebar.number_input(key="seed_input").value == C.DEFAULT_SEED


def test_experiments_run_on_demand(monkeypatch):
    import lip_evaluation as ev
    d_o, h_o = ev.distribution, ev.heatmap
    monkeypatch.setattr(ev, "distribution", lambda p: d_o(p, seeds=C.SWEEP_SEEDS[:3]))
    monkeypatch.setattr(ev, "heatmap", lambda p: h_o(p, hz_grid=(5, 100), rho_grid=(0, 100), seeds=C.HEAT_SEEDS[:2]))
    at = _run()
    for key in ("hz_start", "rho_start", "dist_start", "heat_start"):
        _button(at, key).click().run()
        assert not at.exception, key
    assert any("Die bloße Neuzuordnung der Kunden schließt im Mittel nur" in c.value for c in at.caption)


def test_exact_button_is_disabled_for_large_nets_and_works_for_small_ones():
    at = _run()
    assert _button(at, "exact_start").disabled
    at = _run(lambda a: _apply(a, C.PRESETS["🧲 Ein Start reicht nicht"]))
    assert not _button(at, "exact_start").disabled
    _button(at, "exact_start").click().run()
    assert not at.exception
    assert any("bliebe sie 4,76 % darüber" in t for t in _texts(at))
    at = _run(lambda a: _apply(a, C.PRESETS["🧮 Kleinnetz mit exaktem Optimum"]))
    _button(at, "exact_start").click().run()
    assert not at.exception and any("trifft das Optimum" in t for t in _texts(at))


def test_source_has_explicit_chart_keys_and_locked_axes():
    app = APP.read_text(encoding="utf-8")
    assert all(re.search(r"plotly_chart\(.*key=", line) for line in app.splitlines() if "st.plotly_chart(" in line)
    viz = (ROOT / "lip_visualization.py").read_text(encoding="utf-8")
    assert viz.count("_base(fig") >= 5 and "def lock_axes" in viz
