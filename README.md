# Wert der Information: EVPI und VSS – Streamlit-Demo

Stück der **Optimierung-unter-Unsicherheit-Linie** der „Konzepte“-Reihe für die Website „Sebastian Hanisch – Operations Research und Machine Learning“, und zugleich ihre Wurzel:
anders als die Fall-Demos (ein Anwendungsfall, mehrere Verfahren im Vergleich) zeigt sie **ein** Verfahren, die Wert-der-Information-Analyse, an einem wachsenden Beispiel.
Erst ein **Standort in geschlossener Form** (Newsvendor mit Zukauf und Fehlmenge), dann **sechs Standorte** mit Umlagerung als lineares Programm.
Das Vehikel ist eine Kapazitätsvorhaltung: Kapazität wird vor der Nachfrage gewählt, danach lässt sich Fehlendes nur noch umlagern, zukaufen oder als Fehlmenge bestrafen.

## Warum dieses Problem

Wer unter Unsicherheit plant, stellt zwei Fragen und verwechselt sie gern: **Was wäre es wert, die Nachfrage vorher zu kennen?** (EVPI, Wert der vollständigen Information) und
**Was bringt es, die Streuung überhaupt zu modellieren, statt mit dem Durchschnitt zu planen?** (VSS, Wert der stochastischen Lösung). Beide sind Kostenabstände auf derselben Szenario-Menge,
und sie sind **keine Schranken füreinander**: In der Demo gibt es Einstellungen mit großem EVPI und winzigem VSS (Geld gehört in bessere Prognosen, nicht in ein aufwendigeres Modell),
und Einstellungen mit größerem VSS als EVPI.

## Modell

Sechs Standorte mit mittlerer Nachfrage zwischen 60 und 140 (Zufalls-Seed der Instanz). **Stufe 1:** Kapazität je Standort zu 1 je Einheit, Summe höchstens ein einstellbarer Anteil der Gesamtnachfrage.
**Stufe 2**, nach der Nachfrage: eigene Kapazität deckt eigenen Bedarf, ungenutzte Kapazität kann an andere Standorte umgelagert werden (Transportkosten 0,35 · (0,3 + Abstand), abschaltbar),
Rest per Zukauf (Preis einstellbar, höchstens 50 % der mittleren Nachfrage) oder als Fehlmenge (dreifach bestraft). Die Nachfrage ist lognormal mit Erwartungswert gleich Mittel,
einstellbarer Log-Streuung σ und einem einstellbaren gemeinsamen Faktor ρ. **200 gleich wahrscheinliche Szenarien sind die Verteilung**: Die Demo misst also keine Schätzung aus einer Stichprobe.
Formeln und Herleitung im 📐-Expander der App.

## Methodik

Dieselben Szenarien unter vier Informationsständen, jeweils als **ein** lineares Programm (HiGHS über `scipy.optimize.linprog`; Szenarien einer Gruppe teilen sich einen Plan):

- **EEV:** Plan für die mittlere Nachfrage, über alle Szenarien ausgewertet.
- **RP:** der eine Plan mit den im Mittel niedrigsten Kosten (Verteilung bekannt).
- **Teilinformation:** ein Plan je Stufe des gemeinsamen Faktors (fünf gleich große Stufen).
- **WS (Hellseher):** ein eigener Plan je Szenario.

**EVPI = RP − WS**, **VSS = EEV − RP**, beide in Prozent der Kosten des Plans unter Unsicherheit. Beim einen Standort ist alles geschlossen (lognormale Teilerwartung); dort ist WS = Vorhaltungskosten · Mittel.

## Befunde (gemessen, keine Behauptungen)

Zahlen mit dem Zufalls-Seed der Voreinstellung (7), jeweils in `tests/test_claims.py` belegt; ein Seed ist kein Befund, die Spannweite über drei feste Instanzen steht in Klammern (Median, kleinster bis größter Wert).

| Frage | Befund |
|---|---|
| **Voreinstellung:** lohnt Information, reicht der Durchschnitt? | EVPI 7,4 %, VSS 0,13 % (über drei Instanzen VSS 0,15 bis 0,43 %): Der Durchschnittsplan ist praktisch so gut wie der Plan unter Unsicherheit, Vorwissen wäre bis zu 7,4 % wert. |
| **Was holt ein einzelner gemeinsamer Faktor vom EVPI?** | 39 % in der Voreinstellung, 8 bis 11 % ohne Umlagerung und mit knappem Budget, rund 50 % bei hoher Streuung und weitem Budget. |
| **Wann versagt der Durchschnittsplan?** | Ohne Umlagerung und mit Budget 0,85: VSS 3,8 % (4,4 bis 4,9 % über drei Instanzen). Bei Zukaufpreis 1,2 ohne Umlagerung: VSS 2,2 %. |
| **Ist der Durchschnittsplan bei hoher Streuung automatisch schlecht?** | Nein: bei σ = 0,5, Umlagerung und Budget 1,3 liegt der EVPI bei 19,5 %, der VSS bei 0,14 %. |
| **Kann der VSS größer als der EVPI sein?** | Ja: σ = 0,10, Budget 0,8, keine Umlagerung: VSS 4,1 %, EVPI 1,2 %. |
| **Was bewirkt die Streuung?** | Der EVPI wächst mit σ (mit Umlagerung von 1,6 % bei σ = 0,1 auf 11,4 % bei σ = 0,6). Der VSS steigt nicht mit: mit Umlagerung 0,25 bis 0,39 %, ohne 1,4 bis 2,5 %, ohne Umlagerung fällt er von σ = 0,2 bis 0,6. |
| **Wo liegt der Durchschnittsplan falsch?** | Er kürzt einen Standort bis auf gut die Hälfte der mittleren Nachfrage (Zukauf deckt den Rest im Mittel gerade); der Plan unter Unsicherheit hält dort mehr vor. |
| **Ein Standort** | EVPI 22,5 %, VSS 0,10 %, bester Plan bei 96,8 statt 100: Die Kurve ist um das Optimum flach, deshalb ist der Durchschnittsplan nur wenig schlechter. |

## Ehrliche Grenzen

- **Die Szenarien sind die Verteilung.** Bei einer echten Stichprobe aus unbekannter Verteilung sind EVPI und VSS selbst Schätzungen, und der Optimalwert einer Stichprobe ist nach unten verzerrt. Dieser Fehler ist hier ausgeklammert. Ihn behandelt die [Stichproben-Demo (SAA)](https://github.com/sebastian-hanisch/saa-demo) der Linie.
- **EVPI ist eine Obergrenze.** Kein reales Informationssystem liefert das einzelne Szenario vorab; die Teilinformation zeigt nur, wie viel ein einzelner gemeinsamer Faktor schon holt.
- **Nur der Erwartungswert.** Ein Plan, der im Mittel am billigsten ist, kann im Tail sehr teuer werden; EVPI und VSS sagen darüber nichts. Das Risiko als Ziel zeigt die [CVaR-Demo](https://github.com/sebastian-hanisch/cvar-demo) der Linie.
- **Eine Familie von Instanzen.** Sechs Standorte, lognormal, ein gemeinsamer Faktor, feste Preise und Grenzen. Das Experiment zeigt die Spannweite über drei feste Instanzen, nicht über alle möglichen.
- **Das Bild hängt an der Umlagerung.** Der VSS ist hier vor allem eine Folge der Möglichkeiten nach der Realisierung, nicht der Streuung; mit anderen Kostenstrukturen kann es anders aussehen.
- **Nur ein Informationsstand dazwischen.** Die Teilinformation nutzt den gemeinsamen Faktor in fünf Stufen; andere Teilinformation (einzelne Standorte, verrauschte Hinweise) ist nicht abgebildet.

## Verifikation

- **Kern:** Stufe-2-Block und Kosten an der Mini-Instanz von Hand gerechnet (Umlagerung an und aus, Zukaufgrenze, Fehlmenge), Hellseher kauft genau die Nachfrage vor, Kette WS ≤ Teilinformation ≤ RP ≤ EEV, Streuung null gibt EVPI und VSS gleich null, Szenarien deterministisch.
- **Orakel (`tests/test_oracle_newsvendor_evpi.py`):** dasselbe Modell als eigenes LP in OR-Tools (GLOP, Schleifen statt Blockmatrizen) für alle drei Informationsstrukturen, mit und ohne Umlagerung (Übereinstimmung auf 1e-7);
  ein Standort gegen die geschlossene Form, diese wiederum gegen numerische Integration und gegen das Quantil F⁻¹((s − c)/s); Hellseher-Identität im Mehr-Standort-Fall.
- **Claims (`tests/test_claims.py`):** jede Zahl dieses README, als Band.
- **Presets und Oberfläche:** Vollständigkeit, Werte innerhalb der Grenzen, Permalink begrenzt und rastet ein; AppTest-Rauchtest (jeder Button, jeder Regler am Minimum und Maximum), Footer-Test.

## Dateistruktur

| Datei | Zweck |
|---|---|
| `app.py` | Streamlit-App |
| `nvp_rng.py` | SplitMix64, Standardnormale per Inversion |
| `nvp_scenario.py` | Instanz und Nachfrage-Szenarien |
| `nvp_algorithm.py` | Kern: Stufe-2-Block, ein LP je Informationsstruktur, EVPI/VSS |
| `nvp_closed_form.py` | Ein Standort in geschlossener Form (lognormal) |
| `nvp_evaluation.py` | Kennzahlen, Verdikt-Logik, Sweep über die Streuung |
| `nvp_constants.py` | Regler-Grenzen, feste Annahmen, Farben, Presets |
| `nvp_presets.py` | Permalink (Begrenzen, Einrasten), Presets, Zufalls-Seed-Button |
| `nvp_visualization.py` | Plotly-Abbildungen (Achsen gesperrt) |
| `tools/measure_stueck1.py` | Messreihe für README und Claims |
| `tests/` | Mini-Instanz, Orakel, Claims, Presets, AppTest-Smoke-Test, Footer |
| `requirements.txt` / `requirements-dev.txt` | Laufzeit-Bibliotheken (ungepinnt) / plus pytest und OR-Tools für die Gegenprobe |

## Bewusst nicht umgesetzt

- **Stichprobenfehler und Szenarienzahl:** hier sind die Szenarien die Verteilung; was passiert, wenn sie aus Daten geschätzt werden, ist eine eigene Frage.
- **Risikomaße und Garantien:** nur der Erwartungswert, kein Tail-Risiko, keine Zulässigkeitsgarantie.
- **Mehrstufigkeit:** eine Entscheidung vor der Nachfrage, danach nichts Neues zu entscheiden außer dem Fluss.

## Lokal ausführen

```bash
python3 -m venv venv
source venv/bin/activate          # Windows: venv\Scripts\activate

pip install -r requirements.txt
streamlit run app.py
```

## Tests ausführen

```bash
pip install -r requirements-dev.txt
pytest tests/ -v
```

Gebaut mit Streamlit, Plotly, NumPy und SciPy.

---

Diese Demo ist Teil des Portfolios von [Sebastian Hanisch](https://sebastianhanisch.net) – Operations Research und Machine Learning ([Über mich](https://sebastianhanisch.net/ueber-mich.html)). Mehr zur Reihe: [Unsicherheit: von EVPI bis rollierend](https://sebastianhanisch.net/konzepte-optimierung-unsicherheit.html).
