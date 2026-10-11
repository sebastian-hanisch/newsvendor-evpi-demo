"""Permalink (Begrenzen, Einrasten), Presets und Zufalls-Seed-Button (Standardmuster aus dem Demo-Portfolio)."""

import random
from dataclasses import dataclass

import streamlit as st

import nvp_constants as C


@dataclass(frozen=True)
class SettingSpec:
    url_param: str
    caster: type
    default: object
    lo: float | None = None
    hi: float | None = None
    step: float | None = None
    choices: tuple | None = None


SETTING_SPECS = {
    "sigma_slider": SettingSpec("sigma", float, C.DEFAULT_SIGMA, C.SIGMA_MIN, C.SIGMA_MAX, C.SIGMA_STEP),
    "rho_slider": SettingSpec("rho", float, C.DEFAULT_RHO, C.RHO_MIN, C.RHO_MAX, C.RHO_STEP),
    "budget_slider": SettingSpec("budget", float, C.DEFAULT_BUDGET, C.BUDGET_MIN, C.BUDGET_MAX, C.BUDGET_STEP),
    "spot_slider": SettingSpec("spot", float, C.DEFAULT_SPOT, C.SPOT_MIN, C.SPOT_MAX, C.SPOT_STEP),
    "transfer_radio": SettingSpec("transfer", str, C.DEFAULT_TRANSFER, choices=C.TRANSFER_CHOICES),
    "seed_input": SettingSpec("seed", int, C.DEFAULT_SEED, 0, C.SEED_MAX),
}
PRESET_KEYS = {
    "sigma": "sigma_slider", "rho": "rho_slider", "budget": "budget_slider",
    "spot": "spot_slider", "transfer": "transfer_radio", "seed": "seed_input",
}


def init_session_state_defaults():
    for state_key, spec in SETTING_SPECS.items():
        if state_key not in st.session_state:
            st.session_state[state_key] = spec.default


def bounds(state_key):
    """(min, max, Standard, Schritt) für `st.slider`; der Standardwert ist der Wert im Zustand."""
    spec = SETTING_SPECS[state_key]
    return spec.lo, spec.hi


def snap(spec: SettingSpec, value):
    """Auf die Reglergrenzen begrenzen und auf den Schritt einrasten (Rundungsrauschen der Float-Schritte entfernen)."""
    if spec.choices is not None:
        return value if value in spec.choices else spec.default
    if spec.lo is not None:
        value = max(spec.lo, value)
    if spec.hi is not None:
        value = min(spec.hi, value)
    if spec.step is not None and spec.caster is float:
        value = round(spec.lo + round((value - spec.lo) / spec.step) * spec.step, 6)
    return value


def load_permalink_settings():
    """Einmal je Sitzung: Werte aus der Adresszeile übernehmen, begrenzt und eingerastet."""
    if "permalink_loaded" in st.session_state:
        return
    qp = st.query_params
    for state_key, spec in SETTING_SPECS.items():
        if spec.url_param in qp:
            raw = qp[spec.url_param]
            if isinstance(raw, list):
                raw = raw[0] if raw else ""
            try:
                value = spec.caster(raw)
            except (ValueError, TypeError):
                continue
            st.session_state[state_key] = snap(spec, value)
    st.session_state["permalink_loaded"] = True


def sync_query_params(values):
    """`values`: {state_key: aktueller Wert}; die Adresszeile spiegelt die Konfiguration."""
    try:
        for state_key, value in values.items():
            st.query_params[SETTING_SPECS[state_key].url_param] = str(value)
    except Exception:
        pass


def apply_preset(name):
    for key, state_key in PRESET_KEYS.items():
        if key in C.PRESETS[name]:
            st.session_state[state_key] = C.PRESETS[name][key]


def randomize_seed():
    st.session_state["seed_input"] = random.randint(0, C.SEED_MAX)
