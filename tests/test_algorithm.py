"""Einheiten des Kerns an der Mini-Instanz (zwei Standorte), Ergebnisse von Hand gerechnet."""

import numpy as np
import pytest

import nvp_algorithm as A
import nvp_constants as C
import nvp_scenario as S
from nvp_evaluation import Settings, analyse


def _eval(inst, x, demand_row):
    """Gesamtkosten (Stufe 1 + 2) eines festen Plans für genau ein Szenario."""
    val, _ = A.solve_grouped(inst, np.array([demand_row], dtype=float), np.zeros(1, dtype=int), x_fixed=np.array(x, dtype=float))
    return val


def test_stage2_block_shapes_and_bounds(mini, mini_no_transfer):
    cost, a_cap, a_dem, upper = A.stage2_block(mini)
    assert cost.shape == (8,) and a_cap.shape == (2, 8) and a_dem.shape == (2, 8)
    assert list(cost[:4]) == [0.0, 0.5, 0.5, 0.0]
    assert list(upper[4:6]) == [50.0, 30.0]
    _, _, _, upper_off = A.stage2_block(mini_no_transfer)
    # y[0,1] und y[1,0] gesperrt, y[0,0] und y[1,1] bleiben offen
    assert upper_off[1] == 0.0 and upper_off[2] == 0.0 and np.isinf(upper_off[0]) and np.isinf(upper_off[3])


def test_hand_calculation_with_transfer(mini):
    # x = (80, 80), D = (100, 50): Standort 2 gibt 20 an Standort 1 ab (0,5 je Einheit) -> 160 + 10
    assert _eval(mini, (80, 80), (100, 50)) == pytest.approx(170.0)


def test_hand_calculation_without_transfer(mini_no_transfer):
    # dieselben Zahlen ohne Umlagerung: 20 Einheiten Zukauf zu 2 -> 160 + 40
    assert _eval(mini_no_transfer, (80, 80), (100, 50)) == pytest.approx(200.0)


def test_unmet_demand_is_penalised_beyond_the_spot_limit(mini_no_transfer):
    # x = (0, 60), D = (100, 60): 50 Einheiten Zukauf (Grenze) zu 2, 50 Fehlmenge zu 3 -> 60 + 100 + 150
    assert _eval(mini_no_transfer, (0, 60), (100, 60)) == pytest.approx(310.0)


def test_wait_and_see_buys_exactly_the_demand(mini):
    d = np.array([[100.0, 50.0], [80.0, 90.0]])
    ws, _ = A.solve_grouped(mini, d, np.arange(2))
    assert ws == pytest.approx(1.0 * d.sum(axis=1).mean())


def test_groups_all_equal_means_a_single_plan(mini):
    d = np.array([[100.0, 50.0], [80.0, 90.0], [120.0, 70.0]])
    _, x = A.solve_grouped(mini, d, np.zeros(3, dtype=int))
    assert x.shape == (1, 2)
    _, x_each = A.solve_grouped(mini, d, np.arange(3))
    assert x_each.shape == (3, 2)


def test_z0_groups_are_balanced_and_ordered():
    z0 = np.array([0.3, -1.0, 2.0, -0.2, 1.1, 0.0, -3.0, 0.9, 0.5, -0.5])
    g = A.z0_groups(z0, bins=5)
    assert sorted(np.bincount(g)) == [2, 2, 2, 2, 2]
    assert g[np.argmin(z0)] == 0 and g[np.argmax(z0)] == 4


def test_zero_variance_has_no_information_value():
    r = analyse(Settings(sigma=0.0, seed=11))
    assert r.info.evpi == pytest.approx(0.0, abs=1e-6)
    assert r.info.vss == pytest.approx(0.0, abs=1e-6)


@pytest.mark.parametrize("transfer", ["an", "aus"])
def test_value_chain_is_ordered(transfer):
    r = analyse(Settings(sigma=0.4, budget=0.9, transfer=transfer, seed=3))
    i = r.info
    tol = 1e-6 * i.rp
    assert i.ws <= i.partial + tol and i.partial <= i.rp + tol and i.rp <= i.eev + tol


def test_scenarios_are_deterministic_and_have_the_requested_mean():
    inst = S.make_instance(5, sigma=0.35, rho=0.4, budget_ratio=0.95, spot_mult=1.9, transfer=True)
    d1, z1 = S.demand_scenarios(inst, 5)
    d2, z2 = S.demand_scenarios(inst, 5)
    assert np.array_equal(d1, d2) and np.array_equal(z1, z2)
    assert d1.shape == (C.SCENARIOS, C.J)
    assert np.all(d1 > 0)
    assert d1.mean(axis=0) == pytest.approx(np.asarray(inst.mu), rel=0.12)
