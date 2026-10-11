"""Plotly-Figuren: Informationsleiter, Pläne je Standort, Kostenkurve eines Standorts, Sweep. Alle Achsen fest (fixedrange)."""

import numpy as np
import plotly.graph_objects as go

import nvp_constants as C


def _fixed(fig, height=340):
    fig.update_xaxes(fixedrange=True)
    fig.update_yaxes(fixedrange=True)
    fig.update_layout(height=height, margin=dict(l=10, r=10, t=30, b=10), legend=dict(orientation="h", y=-0.2))
    return fig


def build_ladder(info) -> go.Figure:
    """Erwartete Gesamtkosten je Informationsstand (von „nichts außer dem Mittel“ bis „alles“), Abstand zum Hellseher in %."""
    steps = [
        ("Nur der Durchschnittsfall (EEV)", info.eev, C.COLOR_EEV),
        ("Verteilung bekannt (RP)", info.rp, C.COLOR_RP),
        ("Gemeinsamer Faktor bekannt (5 Stufen)", info.partial, C.COLOR_PARTIAL),
        ("Jedes Szenario bekannt (Hellseher, WS)", info.ws, C.COLOR_WS),
    ]
    fig = go.Figure()
    labels = [s[0] for s in steps]
    for label, value, color in steps:
        extra = 100.0 * (value / info.ws - 1.0)
        fig.add_trace(go.Scatter(
            x=[value], y=[label], mode="markers+text", marker=dict(size=16, color=color), showlegend=False,
            text=[f"{value:.0f}  ({extra:+.1f} % gegen Hellseher)".replace(".", ",")],
            textposition="middle right", hovertemplate=f"{label}<br>%{{x:.1f}}<extra></extra>",
        ))
    lo, hi = info.ws, info.eev
    pad = max(hi - lo, 1.0)
    fig.update_xaxes(title="Erwartete Gesamtkosten", range=[lo - 0.1 * pad, hi + 1.0 * pad])
    fig.update_yaxes(autorange="reversed", categoryorder="array", categoryarray=labels)
    return _fixed(fig, 300)


def build_plans(mu, x_ev, x_rp) -> go.Figure:
    names = [f"Standort {i + 1}" for i in range(len(mu))]
    fig = go.Figure()
    fig.add_trace(go.Bar(x=names, y=list(mu), name="mittlere Nachfrage", marker_color=C.COLOR_MEAN))
    fig.add_trace(go.Bar(x=names, y=list(x_ev), name="Plan für den Durchschnittsfall", marker_color=C.COLOR_EEV))
    fig.add_trace(go.Bar(x=names, y=list(x_rp), name="Plan unter Unsicherheit", marker_color=C.COLOR_RP))
    fig.update_layout(barmode="group")
    fig.update_yaxes(title="Kapazität")
    return _fixed(fig)


def build_single(curve_x, curve_y, values, mean) -> go.Figure:
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=list(curve_x), y=list(curve_y), mode="lines", name="erwartete Kosten", line=dict(color=C.COLOR_RP, width=2)))
    fig.add_trace(go.Scatter(
        x=[values["x_ev"]], y=[values["eev"]], mode="markers", name="Plan für den Durchschnitt (x = Mittel)",
        marker=dict(size=13, color=C.COLOR_EEV)))
    fig.add_trace(go.Scatter(
        x=[values["x_rp"]], y=[values["rp"]], mode="markers", name="bester Plan (Quantil)",
        marker=dict(size=13, color=C.COLOR_RP, symbol="diamond")))
    fig.add_hline(y=values["ws"], line_dash="dot", line_color=C.COLOR_WS, annotation_text="Hellseher (WS)", annotation_position="bottom right")
    fig.update_xaxes(title="vorgehaltene Kapazität x")
    fig.update_yaxes(title="erwartete Kosten", range=[values["ws"] * 0.97, max(curve_y) * 1.01])
    return _fixed(fig)


def build_sweep(rows) -> go.Figure:
    fig = go.Figure()
    styles = {"an": "solid", "aus": "dash"}
    for transfer in C.TRANSFER_CHOICES:
        sub = [r for r in rows if r["transfer"] == transfer]
        x = [r["sigma"] for r in sub]
        fig.add_trace(go.Scatter(
            x=x, y=[r["evpi"] for r in sub], mode="lines+markers", name=f"EVPI, Umlagerung {transfer}",
            line=dict(color=C.COLOR_WS, dash=styles[transfer]),
            error_y=dict(type="data", symmetric=False, array=[r["evpi_high"] - r["evpi"] for r in sub],
                         arrayminus=[r["evpi"] - r["evpi_low"] for r in sub], thickness=1, width=3)))
        fig.add_trace(go.Scatter(
            x=x, y=[r["vss"] for r in sub], mode="lines+markers", name=f"VSS, Umlagerung {transfer}",
            line=dict(color=C.COLOR_EEV, dash=styles[transfer]),
            error_y=dict(type="data", symmetric=False, array=[r["vss_high"] - r["vss"] for r in sub],
                         arrayminus=[r["vss"] - r["vss_low"] for r in sub], thickness=1, width=3)))
    fig.update_xaxes(title="Streuung der Nachfrage (Log-Streuung σ)")
    fig.update_yaxes(title="in % der Kosten des Plans unter Unsicherheit", rangemode="tozero")
    return _fixed(fig, 380)
