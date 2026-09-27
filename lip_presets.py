"""SETTING_SPECS-Permalink-Muster, Presets und Zufalls-Seed-Button (Standardmuster des Portfolios, siehe gm_presets.py in greedy-matching-demo)."""

import math
import random
from dataclasses import dataclass
from typing import Callable, Optional

import streamlit as st

import lip_constants as C


@dataclass(frozen=True)
class SettingSpec:
    url_param: str
    caster: Callable
    default: object
    lo: Optional[float] = None
    hi: Optional[float] = None


SETTING_SPECS = {
    "sites_slider": SettingSpec("sites", int, C.DEFAULT_SITES, C.SITES_MIN, C.SITES_MAX),
    "cust_slider": SettingSpec("customers", int, C.DEFAULT_CUST, C.CUST_MIN, C.CUST_MAX),
    "cv_slider": SettingSpec("cv", int, C.DEFAULT_CV, C.CV_MIN, C.CV_MAX),
    "fixed_slider": SettingSpec("fixed", int, C.DEFAULT_FIXED, C.FIXED_MIN, C.FIXED_MAX),
    "t_slider": SettingSpec("t", int, C.DEFAULT_T, C.T_MIN, C.T_MAX),
    "hz_slider": SettingSpec("hz", int, C.DEFAULT_HZ, C.HZ_MIN, C.HZ_MAX),
    "rho_slider": SettingSpec("rho", int, C.DEFAULT_RHO, C.RHO_MIN, C.RHO_MAX),
    "seed_input": SettingSpec("seed", int, C.DEFAULT_SEED, 0, C.SEED_MAX),
}
PRESET_KEYS = {"sites": "sites_slider", "customers": "cust_slider", "cv": "cv_slider", "fixed": "fixed_slider", "t": "t_slider", "hz": "hz_slider", "rho": "rho_slider", "seed": "seed_input"}
# Alle Regler sind immer sichtbar; KEPT bleibt leer (das Muster für ausblendbare Regler steht in den Schwesterdemos).
KEPT = {}
# Schrittweite der Regler: der Permalink rundet auf das Raster (sonst zeigt der Regler einen Wert, der nicht auf seinem Raster liegt)
STEPS = {"cv_slider": 10, "fixed_slider": 10, "t_slider": 10, "hz_slider": 5, "rho_slider": 5}


def init_session_state_defaults():
    for state_key, spec in SETTING_SPECS.items():
        if state_key not in KEPT and state_key not in st.session_state:       # ausblendbare Regler: siehe seed_widget
            st.session_state[state_key] = spec.default


def seed_widget(state_key):
    """Vor dem Zeichnen eines ausblendbaren Reglers: fehlt sein Zustand, kommt der zuletzt gewählte (oder der Standard-) Wert.
    Ein Wert, der in einem Lauf ohne den Regler in den Zustand des Reglers geschrieben wird, erscheint später als Mindestwert im Regler, während die App mit dem geschriebenen Wert rechnet."""
    if state_key not in st.session_state:
        st.session_state[state_key] = st.session_state.get(KEPT[state_key], SETTING_SPECS[state_key].default)


def stash_kept_widget_state():
    """Permalink und Preset legen den Wert eines ausblendbaren Reglers nur in KEPT ab (der Regler holt ihn sich mit `seed_widget`, sobald er gezeichnet wird)."""
    for state_key, kept in KEPT.items():
        if state_key in st.session_state:
            st.session_state[kept] = st.session_state.pop(state_key)


def bounds(state_key):
    spec = SETTING_SPECS[state_key]
    return spec.lo, spec.hi


def load_permalink_settings():
    if "permalink_loaded" in st.session_state:
        return
    qp = st.query_params
    for state_key, spec in SETTING_SPECS.items():
        if spec.url_param in qp:
            try:
                value = spec.caster(qp[spec.url_param])
                if isinstance(value, float) and not math.isfinite(value):
                    continue
                if spec.lo is not None:
                    value = max(spec.lo, value)
                if spec.hi is not None:
                    value = min(spec.hi, value)
                st.session_state[state_key] = value
                if state_key in KEPT:
                    st.session_state[KEPT[state_key]] = value
            except (ValueError, TypeError):
                pass
    for key, step in STEPS.items():
        if key in st.session_state:
            lo = SETTING_SPECS[key].lo
            st.session_state[key] = int(lo + round((st.session_state[key] - lo) / step) * step)
    stash_kept_widget_state()
    st.session_state["permalink_loaded"] = True


def sync_query_params(values):
    """`values`: {state_key: aktueller Wert}."""
    try:
        for state_key, value in values.items():
            st.query_params[SETTING_SPECS[state_key].url_param] = str(value)
    except Exception:
        pass


def apply_preset(name):
    for key, state_key in PRESET_KEYS.items():
        st.session_state[state_key] = C.PRESETS[name][key]
        if state_key in KEPT:
            st.session_state[KEPT[state_key]] = C.PRESETS[name][key]
    stash_kept_widget_state()


def randomize_seed():
    st.session_state["seed_input"] = random.randint(0, C.SEED_MAX)
