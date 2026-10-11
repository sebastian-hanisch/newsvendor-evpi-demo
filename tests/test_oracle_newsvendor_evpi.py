"""Orakel-Tests (DEMO-PLAYBOOK §12): anderer Rechenweg als der Kern.

1. Dasselbe zweistufige Modell als eigenes LP in OR-Tools (GLOP, Schleifen statt Blockmatrizen) für alle Informationsstrukturen.
2. Ein Standort: Kern-LP gegen die geschlossene Form (lognormal), und die geschlossene Form gegen numerische Integration.
3. Hellseher bei Mehr-Standort-Fall: bei nicht bindendem Budget kauft er je Szenario genau die Nachfrage vor (Identität)."""

import dataclasses
import math

import numpy as np
import pytest

import nvp_algorithm as A
import nvp_closed_form as CF
import nvp_scenario as S
from nvp_scenario import Instance

pywraplp = pytest.importorskip("ortools.linear_solver.pywraplp")


def _glop_value(inst: Instance, demand: np.ndarray, groups: np.ndarray) -> float:
    j_count = inst.n
    s_count = demand.shape[0]
    solver = pywraplp.Solver.CreateSolver("GLOP")
    inf = solver.infinity()
    labels = sorted(set(groups.tolist()))
    x = {(g, j): solver.NumVar(0, inf, f"x{g}_{j}") for g in labels for j in range(j_count)}
    p_group = {g: float((groups == g).sum()) / s_count for g in labels}
    obj = solver.Objective()
    for g in labels:
        solver.Add(sum(x[g, j] for j in range(j_count)) <= inst.budget)
        for j in range(j_count):
            obj.SetCoefficient(x[g, j], p_group[g] * inst.cap_cost)
    for s in range(s_count):
        g = int(groups[s])
        y = {}
        for j in range(j_count):
            for k in range(j_count):
                ub = inf if (inst.transfer or j == k) else 0.0
                y[j, k] = solver.NumVar(0, ub, f"y{s}_{j}_{k}")
                obj.SetCoefficient(y[j, k], inst.transfer_cost[j][k] / s_count)
        for k in range(j_count):
            u = solver.NumVar(0, inst.spot_limit[k], f"u{s}_{k}")
            w = solver.NumVar(0, inf, f"w{s}_{k}")
            obj.SetCoefficient(u, inst.spot[k] / s_count)
            obj.SetCoefficient(w, inst.unmet / s_count)
            solver.Add(sum(y[j, k] for j in range(j_count)) + u + w == float(demand[s, k]))
        for j in range(j_count):
            solver.Add(sum(y[j, k] for k in range(j_count)) <= x[g, j])
    obj.SetMinimization()
    assert solver.Solve() == pywraplp.Solver.OPTIMAL
    return obj.Value()


@pytest.mark.parametrize("transfer", [True, False])
def test_kernel_matches_independent_glop_model(transfer):
    inst = dataclasses.replace(
        S.make_instance(21, sigma=0.4, rho=0.4, budget_ratio=0.9, spot_mult=1.6, transfer=transfer),
        mu=(80.0, 120.0, 100.0), spot=(1.7, 1.5, 1.9), spot_limit=(40.0, 60.0, 50.0),
        transfer_cost=((0.0, 0.3, 0.5), (0.3, 0.0, 0.4), (0.5, 0.4, 0.0)), budget=270.0,
    )
    demand, z0 = S.demand_scenarios(inst, 21, count=12)
    for groups in (np.zeros(12, dtype=int), np.arange(12), A.z0_groups(z0, bins=3)):
        value, _ = A.solve_grouped(inst, demand, groups)
        assert value == pytest.approx(_glop_value(inst, demand, groups), rel=1e-7)


def _one_location(mean=100.0, sigma=0.35, spot=1.9, limit=50.0, unmet=3.0) -> Instance:
    return Instance(
        mu=(mean,), cap_cost=1.0, spot=(spot,), unmet=unmet, spot_limit=(limit,), transfer_cost=((0.0,),),
        transfer=True, budget=1e9, sigma=sigma, rho=0.0,
    )


def test_closed_form_expected_cost_matches_numerical_integration():
    quad = pytest.importorskip("scipy.integrate").quad
    mean, sigma, x, spot, limit, unmet = 100.0, 0.35, 95.0, 1.9, 50.0, 3.0
    mu_log = math.log(mean) - 0.5 * sigma ** 2

    def pdf(d):
        return math.exp(-((math.log(d) - mu_log) ** 2) / (2 * sigma ** 2)) / (d * sigma * math.sqrt(2 * math.pi))

    def stage2(d):
        short = max(d - x, 0.0)
        return spot * min(short, limit) + unmet * max(short - limit, 0.0)

    integral = quad(lambda d: stage2(d) * pdf(d), 1e-9, 5000, points=[x, x + limit], limit=400)[0]
    assert CF.expected_cost(x, mean, sigma, 1.0, spot, limit, unmet) == pytest.approx(x + integral, rel=1e-6)


def test_single_location_lp_matches_closed_form():
    inst = _one_location()
    demand, z0 = S.demand_scenarios(inst, 17, count=1200)
    info = A.analyse_information(inst, demand, z0)
    cf = CF.information_values(inst.mu[0], inst.sigma, inst.cap_cost, inst.spot[0], inst.spot_limit[0], inst.unmet)
    # Stichprobenfehler der 1200 Szenarien: wenige Zehntel Prozent
    assert info.rp == pytest.approx(cf["rp"], rel=0.015)
    assert info.eev == pytest.approx(cf["eev"], rel=0.015)
    assert info.ws == pytest.approx(inst.cap_cost * demand[:, 0].mean(), rel=1e-9)
    assert cf["ws"] == pytest.approx(100.0)
    assert info.x_rp[0] == pytest.approx(cf["x_rp"], rel=0.06)


def test_closed_form_optimum_is_the_critical_fractile_without_limit():
    # ohne Zukaufgrenze und ohne Fehlmenge-Strafe: x* = F^-1((s - c) / s), lognormal
    from scipy.stats import lognorm

    mean, sigma, spot = 100.0, 0.35, 1.9
    x_star = CF.optimum(mean, sigma, 1.0, spot, 1e9, spot)
    expected = lognorm(s=sigma, scale=mean * math.exp(-0.5 * sigma ** 2)).ppf((spot - 1.0) / spot)
    assert x_star == pytest.approx(expected, rel=1e-4)


def test_wait_and_see_identity_for_the_multi_location_case():
    inst = S.make_instance(9, sigma=0.4, rho=0.4, budget_ratio=0.95, spot_mult=1.9, transfer=True)
    inst = dataclasses.replace(inst, budget=1e9)  # Budget bindet nie: der Hellseher kauft je Szenario genau die Nachfrage vor
    demand, z0 = S.demand_scenarios(inst, 9, count=80)
    info = A.analyse_information(inst, demand, z0)
    assert info.ws == pytest.approx(inst.cap_cost * demand.sum(axis=1).mean(), rel=1e-9)
