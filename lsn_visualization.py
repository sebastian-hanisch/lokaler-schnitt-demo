"""Plotly-Abbildungen: Karte, Ordnung nach p/Grad, Konduktanzkurve, Verteilungen und Aufwand gegen die Netzgröße. Alle Achsen sind gesperrt."""

import math

import plotly.graph_objects as go

import lsn_constants as C
import lsn_scenario as S
from lsn_karte import karte

HOEHE = 320
MAX_RANG = 1500          # so viele Ränge zeigt die Ordnung höchstens


def _gesperrt(fig: go.Figure, hoehe: int, **layout) -> go.Figure:
    fig.update_xaxes(fixedrange=True)
    fig.update_yaxes(fixedrange=True)
    fig.update_layout(height=hoehe, margin=dict(l=10, r=10, t=30, b=40), dragmode=False, legend=dict(orientation="h", y=-0.28), **layout)
    return fig


def _positionen(sz: S.Szenario, knoten):
    return {u: sz.position(u) for u in knoten}


def karte_menge(sz: S.Szenario, menge, titel_start: str = "s"):
    """Gefundene Menge (rot), gepflanzte Zielmenge (grün, soweit nicht gefunden), Rest grau; im Hallenverbund ein Ausschnitt um die mittlere Halle."""
    knoten = S.ausschnitt(sz)
    menge = set(menge)

    def farbe(u):
        if u in menge:
            return C.COLOR_MENGE
        if u in sz.sammel:
            return C.COLOR_SAMMEL
        if u in sz.ziel:
            return C.COLOR_ZIEL
        return "#c3cad2"

    def hover(u):
        teile = [sz.platz_name(u)]
        if u in menge:
            teile.append("im Schnitt")
        if u in sz.ziel:
            teile.append("gepflanzt")
        return ", ".join(teile)

    return karte(sz.g, _positionen(sz, knoten), farben=farbe, hover=hover, knoten=knoten, marken={sz.start: (titel_start, "#111111")},
                 hoehe=380 if sz.netz == C.NETZ_HALLEN else 300)


def karte_werte(sz: S.Szenario, werte, titel: str):
    knoten = S.ausschnitt(sz)
    holen = (lambda u: werte.get(u, 0.0)) if isinstance(werte, dict) else (lambda u: float(werte[u]))
    obergrenze = max((holen(u) for u in knoten), default=1.0) or 1.0
    return karte(sz.g, _positionen(sz, knoten), werte={u: holen(u) for u in knoten}, farbtitel=titel, cmin=0.0, cmax=obergrenze,
                 hover=lambda u: f"{sz.platz_name(u)}: {holen(u):.5f}", knoten=knoten, marken={sz.start: ("s", "#d1495b")},
                 hoehe=400 if sz.netz == C.NETZ_HALLEN else 320)


def ordnung(sz: S.Szenario, reihe, werte: dict, groesse: int, normiert: bool = True, titel: str = "p / Grad"):
    """Werte in der Sweep-Reihenfolge; Farbe nach Zielmenge bzw. Sammelpunkt, senkrechte Linie am gewählten Schnitt."""
    reihe = list(reihe)[:MAX_RANG]
    fig = go.Figure()
    gruppen = (
        ("gepflanzt", C.COLOR_ZIEL, [i for i, u in enumerate(reihe) if u in sz.ziel]),
        ("Sammelpunkt", C.COLOR_SAMMEL, [i for i, u in enumerate(reihe) if u in sz.sammel and u not in sz.ziel]),
        ("sonst", C.COLOR_GRAU, [i for i, u in enumerate(reihe) if u not in sz.ziel and u not in sz.sammel]),
    )
    for name, farbe, index in gruppen:
        if not index:
            continue
        y = [werte.get(reihe[i], 0.0) / (max(sz.g.d[reihe[i]], 1) if normiert else 1) for i in index]
        fig.add_trace(go.Scattergl(x=[i + 1 for i in index], y=y, mode="markers", marker=dict(color=farbe, size=6), name=name,
                                   customdata=[reihe[i] for i in index], hovertemplate="Rang %{x}, Platz %{customdata}<br>Wert %{y:.2e}<extra></extra>"))
    if groesse <= len(reihe):
        fig.add_vline(x=groesse + 0.5, line=dict(color=C.COLOR_MENGE, dash="dash"))
        fig.add_annotation(x=groesse + 0.5, y=1, yref="paper", text=f"Schnitt: {groesse}", showarrow=False, bgcolor="rgba(255,255,255,0.88)", font=dict(color="#111111"))
    fig.update_yaxes(type="log", title=titel)
    fig.update_xaxes(title="Rang in der Sweep-Reihenfolge")
    return _gesperrt(fig, HOEHE)


def konduktanzkurve(phis, groesse: int = None, marken=(), laenge: int = None):
    """Konduktanz jedes Anfangsstücks über seine Größe. marken: [(Plätze, Konduktanz, Text)] als Vergleichspunkte (Hallenblöcke)."""
    laenge = min(len(phis), laenge or len(phis))
    fig = go.Figure(go.Scatter(x=list(range(1, laenge + 1)), y=[min(f, 1.0) for f in phis[:laenge]], mode="lines", line=dict(color=C.COLOR_LINIE),
                               name="Anfangsstücke", hovertemplate="Größe %{x}: Konduktanz %{y:.4f}<extra></extra>"))
    sichtbar = [m for m in marken if m[0] <= laenge * 1.05]
    if sichtbar:
        fig.add_trace(go.Scatter(x=[m[0] for m in sichtbar], y=[m[1] for m in sichtbar], mode="markers", marker=dict(color=C.COLOR_ZIEL, size=10, symbol="diamond"),
                                 name="Hallenblöcke (ganze Hallen)", text=[m[2] for m in sichtbar], hovertemplate="%{text}: %{y:.4f}<extra></extra>"))
    if groesse is not None and 1 <= groesse <= laenge:
        fig.add_trace(go.Scatter(x=[groesse], y=[min(phis[groesse - 1], 1.0)], mode="markers", marker=dict(color=C.COLOR_MENGE, size=12), name="gewählt",
                                 hovertemplate="gewählt: %{x}, %{y:.4f}<extra></extra>"))
    fig.update_yaxes(type="log", title="Konduktanz")
    fig.update_xaxes(title="Größe des Anfangsstücks (Plätze)")
    return _gesperrt(fig, HOEHE)


def anteil_kurve(betas, anteile, wahl: float = None):
    fig = go.Figure(go.Scatter(x=list(betas), y=[100 * a for a in anteile], mode="lines+markers", line=dict(color=C.COLOR_LINIE), name="Anteil",
                               hovertemplate="β = %{x}: %{y:.1f} %<extra></extra>"))
    if wahl is not None:
        fig.add_vline(x=wahl, line=dict(color=C.COLOR_MENGE, dash="dash"))
    fig.update_xaxes(type="log", title="Sprungwahrscheinlichkeit β", tickvals=list(betas), ticktext=[f"{b:g}".replace(".", ",") for b in betas])
    fig.update_yaxes(title="Anteil in der Zielmenge in %", rangemode="tozero")
    return _gesperrt(fig, 280, showlegend=False)


def verteilung(mit: dict, ohne: dict):
    """F1 je Netz (Histogramm) für beide Ordnungen."""
    fig = go.Figure()
    for zeile, name, farbe in ((mit, "nach p/Grad", C.COLOR_ZIEL), (ohne, "nach p", C.COLOR_MENGE)):
        fig.add_trace(go.Histogram(x=zeile["f1"], name=name, marker_color=farbe, opacity=0.65, xbins=dict(start=0, end=1.0001, size=0.05)))
    fig.update_xaxes(title="F1 je Netz", range=[0, 1.02])
    fig.update_yaxes(title="Netze")
    return _gesperrt(fig, 280, barmode="overlay")


KURVEN_TEXT = {
    "push": "Push β = 0,006, ε = 3·10⁻⁴",
    "push_traege": "dasselbe träge (ACL)",
    "abgestimmt": "PageRank abgestimmt",
    "gierig": "gierig, abgestimmt",
    "waerme": "Wärmeleitung, abgestimmt",
}


def aufwand_gegen_n(n_reihe: dict, namen, obergrenze: float):
    groessen = sorted(n_reihe)
    fig = go.Figure()
    for name in namen:
        fig.add_trace(go.Scatter(x=groessen, y=[n_reihe[n]["kurven"][name]["zugriffe"] for n in groessen], mode="lines+markers", name=KURVEN_TEXT[name],
                                 line=dict(color=C.COLOR_VERFAHREN[name]), hovertemplate="%{x} Plätze: %{y:,.0f}<extra></extra>"))
    fig.add_trace(go.Scatter(x=groessen, y=[n_reihe[n]["vol"] for n in groessen], mode="lines", name="2m (ganzes Netz)", line=dict(color="black", dash="dot")))
    fig.add_trace(go.Scatter(x=groessen, y=[obergrenze] * len(groessen), mode="lines", name="Obergrenze 1/(β·ε)", line=dict(color="gray", dash="dash")))
    fig.update_xaxes(type="log", title="Plätze im Netz", tickvals=groessen, ticktext=[f"{n:,}".replace(",", " ") for n in groessen])
    fig.update_yaxes(type="log", title="Kantenzugriffe (Median)", range=[math.log10(1000), math.log10(max(obergrenze, max(n_reihe[n]["vol"] for n in groessen)) * 2)])
    return _gesperrt(fig, 380)
