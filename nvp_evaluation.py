"""Kennzahlen, Verdikt-Logik und Sweeps."""

from dataclasses import dataclass
from statistics import median

import nvp_algorithm as A
import nvp_closed_form as CF
import nvp_constants as C
from nvp_scenario import Instance, demand_scenarios, make_instance


@dataclass(frozen=True)
class Settings:
    sigma: float = C.DEFAULT_SIGMA
    rho: float = C.DEFAULT_RHO
    budget: float = C.DEFAULT_BUDGET
    spot: float = C.DEFAULT_SPOT
    transfer: str = C.DEFAULT_TRANSFER
    seed: int = C.DEFAULT_SEED


@dataclass(frozen=True)
class Analysis:
    inst: Instance
    info: A.Information
    evpi_pct: float          # in Prozent der Kosten des Plans unter Unsicherheit
    vss_pct: float
    partial_share: float     # Anteil des EVPI, den die Teilinformation (z0 bekannt) holt, in Prozent
    verdict: str             # 'versagt' | 'reicht_information_lohnt' | 'reicht_information_gering'


def build_instance(settings: Settings, seed: int | None = None) -> Instance:
    return make_instance(
        settings.seed if seed is None else seed,
        sigma=settings.sigma, rho=settings.rho, budget_ratio=settings.budget,
        spot_mult=settings.spot, transfer=settings.transfer == "an",
    )


def verdict_of(evpi_pct: float, vss_pct: float) -> str:
    if vss_pct >= C.VSS_RELEVANT:
        return "versagt"
    return "reicht_information_lohnt" if evpi_pct >= C.EVPI_RELEVANT else "reicht_information_gering"


def analyse(settings: Settings, seed: int | None = None) -> Analysis:
    inst = build_instance(settings, seed)
    s = settings.seed if seed is None else seed
    demand, z0 = demand_scenarios(inst, s)
    info = A.analyse_information(inst, demand, z0)
    evpi_pct = 100.0 * info.evpi / info.rp
    vss_pct = 100.0 * info.vss / info.rp
    share = 100.0 * (info.rp - info.partial) / info.evpi if info.evpi > 1e-9 else 0.0
    return Analysis(inst, info, evpi_pct, vss_pct, share, verdict_of(evpi_pct, vss_pct))


def single_location(settings: Settings) -> dict:
    """Ein Standort mit Mittel 100 und denselben Streuungs-, Preis- und Strafeinstellungen, in geschlossener Form."""
    mean = 100.0
    return {"mean": mean, **CF.information_values(
        mean, settings.sigma, C.CAP_COST, settings.spot, C.SPOT_LIMIT * mean, C.UNMET_MULT * C.CAP_COST)}


def sweep_sigma(settings: Settings) -> list[dict]:
    """EVPI und VSS über die Streuung, Umlagerung an und aus, Median über die festen Instanzen (alle anderen Regler wie eingestellt)."""
    rows = []
    for transfer in C.TRANSFER_CHOICES:
        for sigma in C.SWEEP_SIGMAS:
            cfg = Settings(sigma=sigma, rho=settings.rho, budget=settings.budget, spot=settings.spot, transfer=transfer, seed=settings.seed)
            runs = [analyse(cfg, seed) for seed in C.SWEEP_SEEDS]
            rows.append({
                "transfer": transfer, "sigma": sigma,
                "evpi": median(r.evpi_pct for r in runs), "vss": median(r.vss_pct for r in runs),
                "evpi_low": min(r.evpi_pct for r in runs), "evpi_high": max(r.evpi_pct for r in runs),
                "vss_low": min(r.vss_pct for r in runs), "vss_high": max(r.vss_pct for r in runs),
            })
    return rows
