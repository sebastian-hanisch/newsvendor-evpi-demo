"""Wert der Information: EVPI und VSS - interaktive Konzept-Demo
Sebastian Hanisch - Operations Research und Machine Learning

Lauffähig mit: streamlit run app.py
"""

import streamlit as st

import nvp_constants as C
from nvp_evaluation import Settings, analyse, single_location, sweep_sigma
from nvp_presets import (
    apply_preset,
    bounds,
    init_session_state_defaults,
    load_permalink_settings,
    randomize_seed,
    sync_query_params,
)
from nvp_visualization import build_ladder, build_plans, build_single, build_sweep
import nvp_closed_form as CF

st.set_page_config(page_title="Wert der Information – Sebastian Hanisch", layout="wide")


def _de(value: float, digits: int = 1) -> str:
    return f"{value:.{digits}f}".replace(".", ",")


@st.cache_data(show_spinner=False)
def _analysis(settings):
    return analyse(settings)


@st.cache_data(show_spinner=False)
def _sweep(settings):
    return sweep_sigma(settings)


st.title("🔮 Wert der Information: EVPI und VSS")
st.markdown(
    """
Sie müssen **Kapazität vorhalten, bevor** die Nachfrage bekannt ist. Danach lässt sich Fehlendes nur noch teuer zukaufen oder umlagern.
Diese Demo beantwortet zwei Fragen in Euro und Prozent: **Was wäre es wert, die Nachfrage vorher zu kennen (EVPI)?** und
**Was bringt es, die Streuung überhaupt in die Planung zu nehmen, statt mit dem Durchschnitt zu planen (VSS)?**

Anders als die Fall-Demos zeigt sie **ein** Verfahren, die Wert-der-Information-Analyse, an einem wachsenden Beispiel: erst **ein Standort** in
geschlossener Form, dann **sechs Standorte** mit Umlagerung als lineares Programm. Weiter unten: das Streuungs-Experiment, **🚧 Wo die Annahmen enden**
und der Expander **📐 Mathematische Formulierung**.
"""
)

with st.expander("So funktioniert die Wert-der-Information-Analyse", expanded=True):
    st.markdown(
        """
Dieselben **200 gleich wahrscheinlichen Nachfrage-Szenarien** werden unter vier Informationsständen durchgerechnet:

1. **Durchschnittsfall (EEV):** Sie planen für die mittlere Nachfrage und bezahlen dann, was wirklich eintritt.
2. **Verteilung bekannt (RP):** Sie wählen den einen Plan, der im Mittel über alle Szenarien am billigsten ist.
3. **Hellseher (WS):** Für jedes Szenario gibt es einen eigenen, bestmöglichen Plan, als kennten Sie die Nachfrage vorher.
4. **Teilinformation:** Sie kennen nur den gemeinsamen Faktor der Nachfrage (in fünf Stufen) und planen je Stufe neu.

**EVPI = RP − WS** ist das, was vollständiges Vorwissen höchstens wert wäre. **VSS = EEV − RP** ist das, was das Modellieren der Streuung bringt.
Beides sind Kostenabstände auf derselben Szenario-Menge, also keine Schätzungen aus einer Stichprobe.
        """
    )

if C.PRESETS:
    st.caption("🎯 Schnellstart – ein Beispielszenario laden:")
    cols = st.columns(len(C.PRESETS))
    for col, name in zip(cols, C.PRESETS):
        with col:
            st.button(name, width="stretch", on_click=apply_preset, args=(name,), help=C.PRESET_HELP.get(name, ""), key=f"preset_{name}")

st.caption("🔗 Die Adresszeile oben spiegelt Ihre aktuelle Konfiguration wider – einfach kopieren, um ein Szenario zu teilen.")

load_permalink_settings()
init_session_state_defaults()

with st.sidebar:
    st.header("⚙️ Einstellungen")
    st.markdown("**Nachfrage**")
    sigma = st.slider("Streuung (Log-Streuung σ)", *bounds("sigma_slider"), step=C.SIGMA_STEP, key="sigma_slider",
                      help="Wie stark die Nachfrage um ihren Mittelwert schwankt. 0,35 heißt grob: ein Drittel nach oben oder unten ist normal.")
    rho = st.slider("Gleichlauf der Standorte (ρ)", *bounds("rho_slider"), step=C.RHO_STEP, key="rho_slider",
                    help="Anteil der Schwankung, den alle Standorte gemeinsam haben (ein gemeinsamer Faktor). Bei 0 sind sie unabhängig.")
    st.markdown("**Kosten und Möglichkeiten**")
    budget = st.slider("Budget auf die Kapazität (Anteil der Gesamtnachfrage)", *bounds("budget_slider"), step=C.BUDGET_STEP, key="budget_slider",
                       help="Obergrenze für die Summe aller vorgehaltenen Kapazitäten, als Anteil der mittleren Gesamtnachfrage.")
    spot = st.slider("Zukaufpreis (Vielfaches der Vorhaltungskosten)", *bounds("spot_slider"), step=C.SPOT_STEP, key="spot_slider",
                     help="Was eine fehlende Einheit nachträglich kostet, wenn man sie zukauft (Vorhaltung = 1).")
    transfer = st.radio("Umlagerung zwischen Standorten", C.TRANSFER_CHOICES, key="transfer_radio", horizontal=True,
                        help="An: ungenutzte Kapazität eines Standorts kann den Bedarf eines anderen decken (mit Transportkosten).")
    st.markdown("**Instanz**")
    seed = st.number_input("Zufalls-Seed der Instanz", *bounds("seed_input"), key="seed_input", step=1)
    st.button("🎲 Neue Instanz generieren", width="stretch", on_click=randomize_seed)

sync_query_params({
    "sigma_slider": sigma, "rho_slider": rho, "budget_slider": budget, "spot_slider": spot,
    "transfer_radio": transfer, "seed_input": int(seed),
})

settings = Settings(sigma=float(sigma), rho=float(rho), budget=float(budget), spot=float(spot), transfer=str(transfer), seed=int(seed))

# --- Schritt 1: ein Standort ------------------------------------------------------------------------------------------------------------

st.markdown("## 1️⃣ Der einfachste Fall: ein Standort")
one = single_location(settings)
xs, ys = CF.cost_curve(one["mean"], settings.sigma, C.CAP_COST, settings.spot, C.SPOT_LIMIT * one["mean"], C.UNMET_MULT * C.CAP_COST)
st.markdown(
    f"Ein Standort mit mittlerer Nachfrage **{one['mean']:.0f}**, derselben Streuung und denselben Preisen. Hier geht alles in **geschlossener Form** "
    f"(lognormale Nachfrage). Die Kurve zeigt die erwarteten Gesamtkosten je vorgehaltener Menge: der beste Plan liegt bei **{_de(one['x_rp'])}**, "
    f"der Durchschnittsplan bei **{one['x_ev']:.0f}**."
)
c1, c2, c3 = st.columns(3)
c1.metric("EVPI (ein Standort)", f"{_de(100 * one['evpi'] / one['rp'])} %", delta="in % der Kosten des besten Plans", delta_color="off")
c2.metric("VSS (ein Standort)", f"{_de(100 * one['vss'] / one['rp'], 2)} %", delta="in % der Kosten des besten Plans", delta_color="off")
c3.metric("Bester Plan gegen Durchschnittsplan", f"{_de(one['x_rp'] - one['x_ev'])}".replace("-", "−"), delta="Einheiten Kapazität", delta_color="off")
st.plotly_chart(build_single(xs, ys, one, one["mean"]), width="stretch", key="single_chart")
st.caption(
    "Bei einem Standort ist der Hellseher einfach: Wer die Nachfrage kennt, hält genau sie vor, Kosten = Vorhaltungskosten × Mittel. "
    "Die Kurve ist flach um das Optimum, deshalb ist der Durchschnittsplan hier nur wenig schlechter (kleiner VSS), obwohl Vorwissen viel wert wäre (großer EVPI)."
)

# --- Schritt 2: sechs Standorte ---------------------------------------------------------------------------------------------------------

st.markdown("## 2️⃣ Sechs Standorte mit Umlagerung")
with st.spinner("Löse vier lineare Programme über 200 Szenarien …"):
    a = _analysis(settings)
info = a.info
m1, m2, m3, m4 = st.columns(4)
m1.metric("Kosten bei bekannter Verteilung (RP)", f"{info.rp:,.0f}".replace(",", "."), delta="Referenz", delta_color="off")
m2.metric("EVPI", f"{_de(a.evpi_pct)} %", delta=f"Differenz {info.evpi:,.0f} Kosteneinheiten".replace(",", "."), delta_color="off")
m3.metric("VSS", f"{_de(a.vss_pct, 2)} %", delta=f"Differenz {info.vss:,.0f} Kosteneinheiten".replace(",", "."), delta_color="off")
m4.metric("Teilinformation holt vom EVPI", f"{a.partial_share:.0f} %", delta="gemeinsamer Faktor in 5 Stufen bekannt", delta_color="off")
st.plotly_chart(build_ladder(info), width="stretch", key="ladder_chart")
st.caption("Je weiter unten, desto mehr wissen Sie vor der Entscheidung. Der Abstand zwischen den Zeilen ist der Wert der zusätzlichen Information.")
st.plotly_chart(build_plans(a.inst.mu, info.x_ev, info.x_rp), width="stretch", key="plans_chart")
st.caption(
    "Der Durchschnittsplan kürzt dort, wo Zukauf billiger ist als Vorhaltung, bis der Zukauf im Durchschnittsfall gerade noch reicht "
    "(hier höchstens 50 % der mittleren Nachfrage). Jede Mehrnachfrage danach landet in der dreifach bestraften Fehlmenge: "
    "der Plan unter Unsicherheit hält an solchen Standorten mehr vor."
)

# --- Kernfrage ---------------------------------------------------------------------------------------------------------------------------

st.markdown("## ❓ Kernfrage: Muss man die Streuung modellieren, oder reicht der Durchschnitt?")
if a.verdict == "versagt":
    st.warning(
        f"**Der Durchschnittsplan versagt hier:** er kostet {_de(a.vss_pct, 2)} % mehr als der Plan, der die Streuung kennt (VSS). "
        f"Das Modellieren der Streuung lohnt sich. Zusätzliches Vorwissen wäre noch einmal bis zu {_de(a.evpi_pct)} % wert (EVPI)."
    )
elif a.verdict == "reicht_information_lohnt":
    st.info(
        f"**Der Durchschnittsplan reicht:** er ist nur {_de(a.vss_pct, 2)} % schlechter als der Plan unter Unsicherheit. "
        f"Trotzdem wäre Vorwissen bis zu {_de(a.evpi_pct)} % wert: Geld gehört hier in **bessere Prognosen**, nicht in ein aufwendigeres Planungsmodell."
    )
else:
    st.success(
        f"**Wenig zu gewinnen:** Weder das Modellieren der Streuung ({_de(a.vss_pct, 2)} %) noch vollständiges Vorwissen ({_de(a.evpi_pct)} %) "
        "bringt hier mehr als ein paar Prozent."
    )
st.caption(
    "EVPI und VSS sind keine Schranken füreinander: Beide können klein sein, beide groß, und je nach Einstellung ist eines größer als das andere. "
    f"Schwellen der Meldung: VSS ab {C.VSS_RELEVANT:.0f} %, EVPI ab {C.EVPI_RELEVANT:.0f} %."
)

st.markdown("---")

# --- Experiment --------------------------------------------------------------------------------------------------------------------------

st.subheader("🔬 Experiment: Wie hängen EVPI und VSS an der Streuung, und was macht die Umlagerung?")
st.caption(
    "Median über 3 feste Instanzen (Balken: kleinster bis größter Wert); alle übrigen Regler wie in der Seitenleiste, "
    "nur die Streuung läuft über den Bereich und die Umlagerung steht auf an und aus."
)
with st.spinner("Rechne 36 Analysen (6 Streuungen × 2 Umlagerungen × 3 Instanzen) …"):
    rows = _sweep(settings)
st.plotly_chart(build_sweep(rows), width="stretch", key="sweep_chart")
on = {r["sigma"]: r for r in rows if r["transfer"] == "an"}
off = {r["sigma"]: r for r in rows if r["transfer"] == "aus"}
top = C.SWEEP_SIGMAS[-1]
st.info(
    f"Bei σ = {_de(top, 2)} liegt der VSS mit Umlagerung bei {_de(on[top]['vss'], 2)} %, ohne bei {_de(off[top]['vss'], 2)} %; "
    f"der EVPI liegt bei {_de(on[top]['evpi'])} % beziehungsweise {_de(off[top]['evpi'])} %. "
    "Ob der Durchschnittsplan versagt, hängt also weniger an der Streuung als an den **Möglichkeiten nach der Realisierung**: "
    "Wo Umlagerung den Durchschnittsplan ausgleichen kann, ist er verzeihlich."
)

st.markdown("---")

# --- Grenzen -----------------------------------------------------------------------------------------------------------------------------

st.subheader("🚧 Wo die Annahmen enden")
st.markdown(
    """
| Annahme | Was passiert, wenn sie verletzt ist |
|---|---|
| **Die 200 Szenarien sind die Verteilung** | Bei einer echten Stichprobe aus unbekannter Verteilung ist der Wert des besten Plans nach unten verzerrt: EVPI und VSS einer Stichprobe sind selbst Schätzungen mit Fehler. Hier ist dieser Fehler ausgeklammert. |
| **EVPI ist eine Obergrenze** | Kein reales Informationssystem liefert das einzelne Szenario vorab. Die Teilinformation zeigt, wie viel davon schon ein einzelner gemeinsamer Faktor holt. |
| **Lognormale Nachfrage mit einem gemeinsamen Faktor** | Schwerere Ränder oder Sprünge verändern, wie viel der Durchschnittsplan verschenkt. Hier nicht abgebildet. |
| **Eine Instanz aus sechs Standorten** | Die Zahlen hängen an Instanz und Kosten. Das Experiment zeigt die Spannweite über drei feste Instanzen, nicht über alle möglichen. |
| **Preise und Grenzen sind fest** | Zukauf höchstens 50 % der mittleren Nachfrage, Fehlmenge dreifach bestraft. Andere Verhältnisse verschieben, wo der Durchschnittsplan auf einen Knick fällt. |
"""
)

st.markdown("---")

with st.expander("📐 Mathematische Formulierung"):
    st.markdown(
        r"""
**Modell.** Stufe 1: Kapazität $x_j \ge 0$ je Standort $j$, Kosten $c\,x_j$, Budget $\sum_j x_j \le B$. Stufe 2, nach der Nachfrage $\xi = (D_1,\dots,D_J)$:
Flüsse $y_{jk} \ge 0$ (Kapazität von $j$ deckt Bedarf von $k$, Kosten $t_{jk}$, $t_{jj}=0$), Zukauf $0 \le u_k \le \bar u_k$ zum Preis $s_k$, Fehlmenge
$w_k \ge 0$ zur Strafe $p$:
$$Q(x,\xi)=\min \sum_{j,k} t_{jk}y_{jk}+\sum_k s_k u_k+\sum_k p\,w_k \quad\text{u. d. N.}\quad \sum_k y_{jk}\le x_j,\;\; \sum_j y_{jk}+u_k+w_k=D_k.$$

**Drei Kosten.** Mit $S$ gleich wahrscheinlichen Szenarien $\xi_s$:
$$\mathrm{RP}=\min_x\; c\,\mathbf 1^\top x+\tfrac1S\sum_s Q(x,\xi_s),\qquad
\mathrm{WS}=\tfrac1S\sum_s \min_{x}\big[c\,\mathbf 1^\top x+Q(x,\xi_s)\big],$$
$$\mathrm{EEV}=c\,\mathbf 1^\top \bar x+\tfrac1S\sum_s Q(\bar x,\xi_s),\qquad \bar x \in \arg\min_x\; c\,\mathbf 1^\top x+Q(x,\bar\xi),\;\; \bar\xi=\tfrac1S\sum_s\xi_s.$$

**Werte der Information.** $\mathrm{EVPI}=\mathrm{RP}-\mathrm{WS}\ge 0$ und $\mathrm{VSS}=\mathrm{EEV}-\mathrm{RP}\ge 0$, also $\mathrm{WS}\le \mathrm{RP}\le \mathrm{EEV}$.
Der erste Schritt gilt, weil jede Entscheidung, die für alle Szenarien gleich ist, auch je Szenario erlaubt wäre. Der zweite, weil $\bar x$ für das Problem
unter Unsicherheit zulässig, aber nicht optimal sein muss (vorausgesetzt: $\bar x$ ist für jede Nachfrage zulässig, hier durch die Fehlmenge gesichert).
Die Teilinformation (Plan je Stufe $g$ von $z_0$) liegt dazwischen: $\mathrm{RP}\ge \mathrm{Partial}\ge \mathrm{WS}$.

**Ein Standort in geschlossener Form.** Für $D$ lognormal mit Erwartungswert $\mu$ und Log-Streuung $\sigma$ sei $L(a)=\mathbb E[(D-a)^+]=\mu\,\Phi(d+\sigma)-a\,\Phi(d)$ mit
$d=\big(\ln(\mu/a)-\sigma^2/2\big)/\sigma$. Die erwarteten Kosten bei Kapazität $x$ sind $c\,x+s\,[L(x)-L(x+u)]+p\,L(x+u)$. Ist $s>c$, kauft der Hellseher genau $D$ vor:
$\mathrm{WS}=c\,\mu$. Ohne Zukaufgrenze und ohne Strafe ist das Optimum das Quantil $F^{-1}\!\big((s-c)/s\big)$ (kritisches Verhältnis).

**Literatur.** Die Begriffe EVPI und VSS folgen der Lehrbuchdarstellung bei Birge & Louveaux, *Introduction to Stochastic Programming* (Springer, 2. Aufl. 2011);
das kritische Verhältnis geht auf Arrow, Harris & Marschak, *Optimal Inventory Policy*, Econometrica 19(3), 1951, S. 250–272 zurück (dort in einem allgemeineren Modell).
Das Lehrbuch war für diese Demo nicht im Volltext zugänglich; die Definitionen wurden über mehrere Sekundärquellen bestätigt und im Test an Beispielen nachgerechnet.
        """
    )

st.markdown("---")
st.caption(
    "Diese Demo ist Teil des Portfolios von [Sebastian Hanisch](https://sebastianhanisch.net) – "
    "Operations Research und Machine Learning ([Über mich](https://sebastianhanisch.net/ueber-mich.html)). "
    "Mehr zu den Demos: [Interaktive Demos](https://sebastianhanisch.net/demos.html)."
)
