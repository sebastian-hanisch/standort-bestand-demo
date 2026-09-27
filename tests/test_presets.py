"""Presets: vollständig, in den Grenzen, auf dem Raster der Regler, und jedes Beispiel zeigt, was sein Name verspricht (die Zahlen selbst belegt test_claims.py)."""

import pytest

import lip_constants as C
import lip_evaluation as ev
import lip_presets as P

KEYS = set(P.PRESET_KEYS)


def test_every_preset_has_help_and_all_keys():
    assert set(C.PRESETS) == set(C.PRESET_HELP) and len(C.PRESETS) == 8
    assert all(C.PRESET_HELP[name].strip() for name in C.PRESETS)
    for name, p in C.PRESETS.items():
        assert set(p) == KEYS, name


@pytest.mark.parametrize("name", list(C.PRESETS))
def test_preset_values_are_inside_the_bounds_and_on_the_slider_grid(name):
    p = C.PRESETS[name]
    for key, state_key in P.PRESET_KEYS.items():
        spec = P.SETTING_SPECS[state_key]
        assert spec.lo <= p[key] <= spec.hi, (name, key)
        if state_key in P.STEPS:
            assert (p[key] - spec.lo) % P.STEPS[state_key] == 0, (name, key)


def test_defaults_are_on_the_slider_grid():
    for state_key, step in P.STEPS.items():
        spec = P.SETTING_SPECS[state_key]
        assert (spec.default - spec.lo) % step == 0


def test_setting_specs_have_room_to_move():
    """Ein Regler mit lo == hi würde Streamlit abstürzen lassen."""
    assert all(spec.lo < spec.hi for spec in P.SETTING_SPECS.values())


def test_presets_use_seeds_outside_the_distribution_set():
    for name, p in C.PRESETS.items():
        assert p["seed"] not in C.DIST_SEEDS, name


def test_each_preset_shows_the_effect_its_name_promises():
    a = {name: ev.analyse(ev.Params(**p)) for name, p in C.PRESETS.items()}
    assert len(a["🏭 Wenige große Lager"]["joint"].open) < len(a["🗺️ Standardnetz"]["joint"].open) and a["🏭 Wenige große Lager"]["gap"] > a["🗺️ Standardnetz"]["gap"]
    assert a["🔗 Korrelierte Nachfrage"]["gap"] < 0.01 and len(a["🔗 Korrelierte Nachfrage"]["joint"].open) == len(a["🔗 Korrelierte Nachfrage"]["naive"].open)
    assert a["💤 Bestand kaum relevant"]["gap"] == 0.0
    assert a["🎲 Stark schwankende Nachfrage"]["gap"] > a["🗺️ Standardnetz"]["gap"] and a["🚚 Billiger Transport"]["gap"] > a["🗺️ Standardnetz"]["gap"]
    assert ev.exact_allowed(ev.Params(**C.PRESETS["🧮 Kleinnetz mit exaktem Optimum"])) and ev.exact_allowed(ev.Params(**C.PRESETS["🧲 Ein Start reicht nicht"]))


def test_the_standard_preset_is_the_default_configuration():
    assert C.PRESETS["🗺️ Standardnetz"] == {"sites": C.DEFAULT_SITES, "customers": C.DEFAULT_CUST, "cv": C.DEFAULT_CV, "fixed": C.DEFAULT_FIXED, "t": C.DEFAULT_T, "hz": C.DEFAULT_HZ, "rho": C.DEFAULT_RHO, "seed": C.DEFAULT_SEED}
    assert ev.Params() == ev.Params(**C.PRESETS["🗺️ Standardnetz"])
