"""Jede Zahl aus README und App-Text wird hier nachgerechnet (Bänder statt exakter Werte: CI installiert die neuesten numpy/scipy)."""

import pytest

import nvp_constants as C
import nvp_evaluation as ev


@pytest.fixture(scope="module")
def presets():
    return {name: ev.analyse(ev.Settings(**p)) for name, p in C.PRESETS.items()}


def test_standard_case_information_is_valuable_but_the_average_plan_is_fine(presets):
    a = presets["Standardfall (Voreinstellung)"]
    assert 7.0 <= a.evpi_pct <= 7.9
    assert a.vss_pct < 0.3
    assert 36 <= a.partial_share <= 42
    assert a.verdict == "reicht_information_lohnt"


def test_high_spread_with_slack_budget_has_evpi_near_twenty_percent(presets):
    a = presets["Durchschnittsplan reicht"]
    assert 19.0 <= a.evpi_pct <= 20.0
    assert a.vss_pct < 0.3
    assert 47 <= a.partial_share <= 53


def test_without_transfer_and_tight_budget_the_average_plan_fails(presets):
    a = presets["Durchschnittsplan versagt"]
    assert 3.3 <= a.vss_pct <= 4.2
    assert 9.5 <= a.evpi_pct <= 10.6
    assert 8 <= a.partial_share <= 14
    assert a.verdict == "versagt"


def test_cheap_spot_market_makes_the_average_plan_fail_too(presets):
    a = presets["Zukauf fast so teuer wie Vorhaltung"]
    assert 1.9 <= a.vss_pct <= 2.6
    assert 14.5 <= a.evpi_pct <= 15.6
    assert a.verdict == "versagt"


def test_the_average_plan_cuts_a_location_down_to_where_the_spot_limit_just_covers_the_mean(presets):
    a = presets["Durchschnittsplan versagt"]
    ratios = [x / m for x, m in zip(a.info.x_ev, a.inst.mu)]
    cut = min(range(len(ratios)), key=ratios.__getitem__)
    assert 0.45 <= ratios[cut] <= 0.6                    # Zukaufgrenze C.SPOT_LIMIT = 0,5: Vorhaltung + Zukauf deckt im Mittel gerade
    assert a.info.x_rp[cut] > a.info.x_ev[cut] + 5.0     # der Plan unter Unsicherheit hält dort mehr vor


def test_vss_can_exceed_evpi(presets):
    a = presets["Kaum Streuung, VSS größer als EVPI"]
    assert a.vss_pct > a.evpi_pct
    assert 3.5 <= a.vss_pct <= 4.7 and 0.9 <= a.evpi_pct <= 1.5


def test_single_location_closed_form_numbers():
    one = ev.single_location(ev.Settings())
    assert 22.0 <= 100 * one["evpi"] / one["rp"] <= 23.0
    assert 0.05 <= 100 * one["vss"] / one["rp"] <= 0.2
    assert 96.0 <= one["x_rp"] <= 97.5
    assert one["ws"] == pytest.approx(100.0)


@pytest.fixture(scope="module")
def sweep():
    return ev.sweep_sigma(ev.Settings())


def test_transfer_keeps_the_vss_below_half_a_percent(sweep):
    on = [r["vss"] for r in sweep if r["transfer"] == "an"]
    assert max(on) < 0.5
    assert 0.2 <= min(on)


def test_without_transfer_the_vss_is_between_one_and_three_percent(sweep):
    off = [r["vss"] for r in sweep if r["transfer"] == "aus"]
    assert 1.0 <= min(off) and max(off) <= 3.0


def test_evpi_grows_with_the_spread(sweep):
    for transfer in C.TRANSFER_CHOICES:
        values = [r["evpi"] for r in sweep if r["transfer"] == transfer]
        assert all(b > a for a, b in zip(values, values[1:]))


def test_vss_is_not_monotone_in_the_spread_without_transfer(sweep):
    # Aussage im README: der VSS steigt nicht mit der Streuung, ohne Umlagerung fällt er von σ = 0,2 bis 0,6
    off = {r["sigma"]: r["vss"] for r in sweep if r["transfer"] == "aus"}
    assert off[0.6] < off[0.2]
