"""Messreihe für README und tests/test_claims.py (Python: _venvs/test). Gibt alle Zahlen aus, die im README stehen."""

import sys
from pathlib import Path
from statistics import median

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import nvp_constants as C  # noqa: E402
from nvp_evaluation import Settings, analyse, single_location, sweep_sigma  # noqa: E402


def line(name, a):
    i = a.info
    return (f"{name:<38} RP {i.rp:7.1f} EEV {i.eev:7.1f} Teil {i.partial:7.1f} WS {i.ws:7.1f} | EVPI {a.evpi_pct:5.2f} % "
            f"VSS {a.vss_pct:5.2f} % Teilinfo {a.partial_share:4.0f} % | {a.verdict}")


def main():
    print("== Presets (Zufalls-Seed der Voreinstellung)")
    for name, p in C.PRESETS.items():
        s = Settings(**p)
        print(line(name, analyse(s)))
    print("== Presets über die drei festen Instanzen (Median)")
    for name, p in C.PRESETS.items():
        s = Settings(**p)
        runs = [analyse(s, seed) for seed in C.SWEEP_SEEDS]
        print(f"{name:<38} EVPI {median(r.evpi_pct for r in runs):5.2f} (min {min(r.evpi_pct for r in runs):5.2f}, max {max(r.evpi_pct for r in runs):5.2f}) "
              f"VSS {median(r.vss_pct for r in runs):5.2f} (min {min(r.vss_pct for r in runs):5.2f}, max {max(r.vss_pct for r in runs):5.2f}) "
              f"Teilinfo {median(r.partial_share for r in runs):4.0f} %  Urteile {[r.verdict for r in runs]}")
    print("== Ein Standort, Voreinstellung")
    one = single_location(Settings())
    print({k: round(v, 3) for k, v in one.items()}, "EVPI %", round(100 * one["evpi"] / one["rp"], 2), "VSS %", round(100 * one["vss"] / one["rp"], 3))
    print("== Sweep über sigma (Voreinstellung der übrigen Regler)")
    for r in sweep_sigma(Settings()):
        print({k: (round(v, 2) if isinstance(v, float) else v) for k, v in r.items()})


if __name__ == "__main__":
    main()
