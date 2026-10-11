"""Konstanten: Regler-Grenzen, feste Annahmen, Farben, Presets und Schwellen der Verdikte."""

# --- Vehikel: Kapazitätsvorhaltung mit Zukauf, Umlagerung und Fehlmenge --------------------------------------------------------------------
J = 6                       # Standorte
MU_LOW, MU_HIGH = 60, 140   # mittlere Nachfrage je Standort (ganzzahlig, aus dem Zufalls-Seed der Instanz)
CAP_COST = 1.0              # Kosten je vorgehaltener Kapazitätseinheit (Stufe 1)
SPOT_JITTER = 0.1           # Zukaufpreis je Standort: s_mult mal Gleichverteilung in [1 - 0,1; 1 + 0,1]
UNMET_MULT = 3.0            # Strafe je Fehlmenge: 3 mal Kapazitätskosten
SPOT_LIMIT = 0.5            # Zukauf höchstens 50 % der mittleren Nachfrage des Standorts
TRANSFER_BASE, TRANSFER_SCALE = 0.3, 0.35   # Umlagerung j -> k: 0,35 * (0,3 + Abstand), Abstand in der Einheitsfläche
SCENARIOS = 200             # gleich wahrscheinliche Szenarien: sie SIND hier die Verteilung (kein Stichprobenfehler)
Z0_BINS = 5                 # Stufen der Teilinformation "gemeinsamer Faktor bekannt"

# --- Regler ------------------------------------------------------------------------------------------------------------------------------
SIGMA_MIN, SIGMA_MAX, SIGMA_STEP, DEFAULT_SIGMA = 0.10, 0.60, 0.05, 0.35
RHO_MIN, RHO_MAX, RHO_STEP, DEFAULT_RHO = 0.0, 0.8, 0.1, 0.4
BUDGET_MIN, BUDGET_MAX, BUDGET_STEP, DEFAULT_BUDGET = 0.70, 1.30, 0.05, 0.95
SPOT_MIN, SPOT_MAX, SPOT_STEP, DEFAULT_SPOT = 1.2, 2.4, 0.1, 1.9
SEED_MAX, DEFAULT_SEED = 999999, 7
TRANSFER_CHOICES = ("an", "aus")
DEFAULT_TRANSFER = "an"
SCENARIO_SEED_OFFSET = 7_000_003   # der Szenarienstrom hängt am Zufalls-Seed der Instanz, aber nicht an dessen Standort-Strom

# --- Sweeps (vorgerechnet, siehe generate_precomputed.py) ---------------------------------------------------------------------------------
SWEEP_SEEDS = (100000, 100001, 100002)   # feste Instanzen: nie ein einzelner Seed als Befund
SWEEP_SIGMAS = (0.10, 0.20, 0.30, 0.40, 0.50, 0.60)

# --- Verdikte (Prozent der Kosten des Plans unter Unsicherheit) ---------------------------------------------------------------------------
VSS_RELEVANT = 1.0          # ab hier trägt der Durchschnittsplan nachweislich nicht
EVPI_RELEVANT = 2.0         # darunter lohnt zusätzliche Information kaum

# --- Farben ------------------------------------------------------------------------------------------------------------------------------
COLOR_RP = "#2F6B65"
COLOR_EEV = "#B5651D"
COLOR_WS = "#4c78a8"
COLOR_PARTIAL = "#8c6bb1"
COLOR_MEAN = "rgba(150,150,150,0.75)"

PRESETS = {
    "Standardfall (Voreinstellung)": {
        "sigma": DEFAULT_SIGMA, "rho": DEFAULT_RHO, "budget": DEFAULT_BUDGET, "spot": DEFAULT_SPOT,
        "transfer": DEFAULT_TRANSFER, "seed": DEFAULT_SEED,
    },
    "Durchschnittsplan reicht": {
        "sigma": 0.50, "rho": DEFAULT_RHO, "budget": 1.30, "spot": DEFAULT_SPOT,
        "transfer": "an", "seed": DEFAULT_SEED,
    },
    "Durchschnittsplan versagt": {
        "sigma": DEFAULT_SIGMA, "rho": DEFAULT_RHO, "budget": 0.85, "spot": DEFAULT_SPOT,
        "transfer": "aus", "seed": DEFAULT_SEED,
    },
    "Zukauf fast so teuer wie Vorhaltung": {
        "sigma": DEFAULT_SIGMA, "rho": DEFAULT_RHO, "budget": 1.30, "spot": 1.2,
        "transfer": "aus", "seed": DEFAULT_SEED,
    },
    "Kaum Streuung, VSS größer als EVPI": {
        "sigma": 0.10, "rho": DEFAULT_RHO, "budget": 0.80, "spot": DEFAULT_SPOT,
        "transfer": "aus", "seed": DEFAULT_SEED,
    },
}
PRESET_HELP = {
    "Standardfall (Voreinstellung)": "Sechs Standorte, Streuung 35 %, Umlagerung an, Budget 95 % der mittleren Nachfrage.",
    "Durchschnittsplan reicht": "Hohe Streuung, aber Umlagerung und reichlich Budget: Information wäre wertvoll, der Durchschnittsplan ist trotzdem fast optimal.",
    "Durchschnittsplan versagt": "Ohne Umlagerung und mit knappem Budget setzt der Durchschnittsplan genau auf die Zukaufgrenze.",
    "Zukauf fast so teuer wie Vorhaltung": "Zukauf nur etwa 20 % über den Vorhaltungskosten (Preis 1,2), ohne Umlagerung und mit weitem Budget.",
    "Kaum Streuung, VSS größer als EVPI": "Streuung 10 %, knappes Budget, keine Umlagerung: Vorwissen wäre kaum etwas wert, das Mitdenken der Streuung aber schon.",
}
