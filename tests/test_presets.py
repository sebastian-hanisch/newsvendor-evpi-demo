"""Presets: Vollständigkeit, gültige Werte, Standard-Preset = Standardeinstellungen; Permalink begrenzt und rastet ein."""

import pytest

import nvp_constants as C
import nvp_evaluation as ev
import nvp_presets as P


def test_every_preset_has_help_and_all_keys():
    assert set(C.PRESETS) == set(C.PRESET_HELP)
    for name, preset in C.PRESETS.items():
        assert set(preset) == set(P.PRESET_KEYS), name
        assert C.PRESET_HELP[name]


def test_preset_values_are_inside_the_bounds():
    for name, preset in C.PRESETS.items():
        for key, state_key in P.PRESET_KEYS.items():
            spec = P.SETTING_SPECS[state_key]
            value = preset[key]
            if spec.choices is not None:
                assert value in spec.choices, (name, key)
            else:
                assert spec.lo <= value <= spec.hi, (name, key)
                if spec.step is not None:
                    assert P.snap(spec, value) == pytest.approx(value), (name, key)


def test_default_preset_equals_the_default_settings():
    assert ev.Settings(**C.PRESETS["Standardfall (Voreinstellung)"]) == ev.Settings()


def test_setting_specs_cover_every_preset_key():
    assert set(P.PRESET_KEYS.values()) == set(P.SETTING_SPECS)


def test_snap_clamps_and_rounds_to_the_step():
    spec = P.SETTING_SPECS["sigma_slider"]
    assert P.snap(spec, 9.0) == C.SIGMA_MAX
    assert P.snap(spec, -1.0) == C.SIGMA_MIN
    assert P.snap(spec, 0.3567) == pytest.approx(0.35)
    assert P.snap(P.SETTING_SPECS["transfer_radio"], "vielleicht") == C.DEFAULT_TRANSFER


def test_sweep_uses_the_fixed_instances_and_a_consistent_band():
    rows = ev.sweep_sigma(ev.Settings())
    assert len(rows) == 2 * len(C.SWEEP_SIGMAS)
    for r in rows:
        assert r["evpi_low"] <= r["evpi"] <= r["evpi_high"]
        assert r["vss_low"] <= r["vss"] <= r["vss_high"]
