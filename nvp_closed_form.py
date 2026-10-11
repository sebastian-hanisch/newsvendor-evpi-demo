"""Der einfachste Fall in geschlossener Form: ein Standort, lognormale Nachfrage (Newsvendor mit Zukauf und Fehlmenge).

Kosten bei Kapazität x: c x + s E[min((D-x)+, u)] + p E[((D-x)+ - u)+] mit Zukaufpreis s, Zukaufgrenze u, Strafe p.
Mit L(a) = E[(D-a)+] (lognormal geschlossen) ist E[min((D-x)+, u)] = L(x) - L(x+u).
Wait-and-see: ist D bekannt, kauft man genau D vor (Kosten c D), also WS = c E[D] (gilt für s > c)."""

import math

import numpy as np
from scipy.optimize import minimize_scalar


def _phi(z: float) -> float:
    return 0.5 * (1.0 + math.erf(z / math.sqrt(2.0)))


def call(mean: float, sigma: float, a: float) -> float:
    """L(a) = E[(D - a)+] für D lognormal mit Erwartungswert `mean` und Log-Streuung `sigma`."""
    if a <= 0.0:
        return mean - a
    d2 = (math.log(mean / a) - 0.5 * sigma ** 2) / sigma
    return mean * _phi(d2 + sigma) - a * _phi(d2)


def expected_cost(x: float, mean: float, sigma: float, cap_cost: float, spot: float, limit: float, unmet: float) -> float:
    covered = call(mean, sigma, x) - call(mean, sigma, x + limit)
    beyond = call(mean, sigma, x + limit)
    return cap_cost * x + spot * covered + unmet * beyond


def optimum(mean: float, sigma: float, cap_cost: float, spot: float, limit: float, unmet: float) -> float:
    """Kostenminimale Kapazität x* (die Kostenfunktion ist konvex: begrenzte Skalarsuche genügt)."""
    res = minimize_scalar(
        lambda x: expected_cost(x, mean, sigma, cap_cost, spot, limit, unmet),
        bounds=(0.0, mean * math.exp(4.0 * sigma)), method="bounded", options={"xatol": 1e-9},
    )
    return float(res.x)


def information_values(mean: float, sigma: float, cap_cost: float, spot: float, limit: float, unmet: float) -> dict:
    """RP, WS, EEV, EVPI, VSS und die Pläne x_RP, x_EV (= mean) in geschlossener Form."""
    x_rp = optimum(mean, sigma, cap_cost, spot, limit, unmet)
    rp = expected_cost(x_rp, mean, sigma, cap_cost, spot, limit, unmet)
    eev = expected_cost(mean, mean, sigma, cap_cost, spot, limit, unmet)
    ws = cap_cost * mean
    return {"x_rp": x_rp, "x_ev": mean, "rp": rp, "eev": eev, "ws": ws, "evpi": rp - ws, "vss": eev - rp}


def cost_curve(mean: float, sigma: float, cap_cost: float, spot: float, limit: float, unmet: float, points: int = 120):
    xs = np.linspace(0.45 * mean, 1.8 * mean, points)
    return xs, np.array([expected_cost(float(x), mean, sigma, cap_cost, spot, limit, unmet) for x in xs])
