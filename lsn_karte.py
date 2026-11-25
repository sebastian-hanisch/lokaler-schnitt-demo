"""Karte eines Netzes (oder eines Ausschnitts davon) als Plotly-Figur. Ohne Streamlit.

Nach dem gemeinsamen Baustein `trz_karte.py` der Reihe „Irrfahrten auf Netzen“, hier für Netze als Nachbarlisten mit eigenen Koordinaten und für Ausschnitte großer
Netze. Beschriftungen sind Annotationen, ausgewählte wie nicht ausgewählte Punkte behalten die volle Deckkraft, die Achsen sind gesperrt."""

import plotly.graph_objects as go

FARBE_KANTE = "rgba(130,130,130,0.55)"
FARBE_KNOTEN = "#9aa5b1"
GROSS_AB = 1500             # ab so vielen gezeichneten Punkten WebGL (Scattergl)


def knotengroesse(n: int) -> int:
    if n <= 10:
        return 30
    if n <= 100:
        return 14
    if n <= 700:
        return 8
    if n <= 2000:
        return 5
    return 3


def _linien(g, pos, sichtbar):
    xs, ys = [], []
    menge = set(sichtbar)
    for u in sichtbar:
        for v in g.nb[u]:
            if u < v and v in menge:
                xs += [pos[u][0], pos[v][0], None]
                ys += [pos[u][1], pos[v][1], None]
    return xs, ys


def karte(g, pos, werte=None, farbtitel: str = "", farbskala="Viridis", cmin=None, cmax=None, farben=None, marken=None, hover=None, knoten=None, hoehe: int = 360,
          beschriftung: bool = None) -> go.Figure:
    """Karte.

    pos: Koordinaten je Knoten (Folge oder Wörterbuch). knoten: nur diese zeichnen (sonst alle). werte: je Knoten (Wörterbuch oder Folge) eine Zahl für die Farbe,
    oder farben: je gezeichnetem Knoten eine feste Farbe. marken: {Knoten: (Kurzzeichen, Farbe)}. hover: Funktion Knoten → Text. beschriftung: Knotennummern
    anzeigen (Standard: nur bis 10 Knoten)."""
    sichtbar = list(range(g.n)) if knoten is None else list(knoten)
    n = len(sichtbar)
    fig = go.Figure()
    spur = go.Scattergl if n > GROSS_AB else go.Scatter
    xs, ys = _linien(g, pos, sichtbar)
    fig.add_trace(spur(x=xs, y=ys, mode="lines", line=dict(color=FARBE_KANTE, width=0.5 if n > 150 else 1.4), hoverinfo="skip", showlegend=False))
    groesse = knotengroesse(n)
    marker = dict(size=groesse, line=dict(width=1 if n <= 700 else 0, color="rgba(60,60,60,0.7)"))
    if farben is not None:
        marker["color"] = [farben(u) for u in sichtbar]
    elif werte is not None:
        holen = (lambda u: werte.get(u, 0.0)) if isinstance(werte, dict) else (lambda u: werte[u])
        marker.update(color=[float(holen(u)) for u in sichtbar], colorscale=farbskala, showscale=True,
                      colorbar=dict(title=dict(text=farbtitel, side="top"), orientation="h", y=-0.12, thickness=10, len=0.8, nticks=5))
        if cmin is not None:
            marker.update(cmin=cmin, cmax=cmax)
    else:
        marker["color"] = FARBE_KNOTEN
    texte = [hover(u) if hover else str(u) for u in sichtbar]
    fig.add_trace(spur(x=[pos[u][0] for u in sichtbar], y=[pos[u][1] for u in sichtbar], mode="markers", marker=marker, customdata=sichtbar, text=texte,
                       hovertemplate="%{text}<extra></extra>", showlegend=False, selected=dict(marker=dict(opacity=1)), unselected=dict(marker=dict(opacity=1))))
    marken = marken or {}
    if beschriftung is None:
        beschriftung = n <= 10
    if beschriftung:
        for u in sichtbar:
            fig.add_annotation(x=pos[u][0], y=pos[u][1], text=str(u), showarrow=False, font=dict(size=13, color="#111111"), bgcolor="rgba(255,255,255,0.75)")
    for nummer, (u, (zeichen, farbe)) in enumerate(marken.items()):
        fig.add_trace(go.Scatter(x=[pos[u][0]], y=[pos[u][1]], mode="markers", marker=dict(size=groesse + 9, color="rgba(0,0,0,0)", line=dict(width=3, color=farbe)),
                                 hoverinfo="skip", showlegend=False))
        ax = 0 if len(marken) == 1 else (-24 if nummer % 2 == 0 else 24)
        fig.add_annotation(x=pos[u][0], y=pos[u][1], text=f"<b>{zeichen}</b>", showarrow=True, arrowhead=0, ax=ax, ay=-28, font=dict(size=13, color="#ffffff"),
                           bgcolor=farbe, arrowcolor=farbe)
    xs_alle = [pos[u][0] for u in sichtbar]
    ys_alle = [pos[u][1] for u in sichtbar]
    rand = 0.35 if n <= 10 else 0.8
    # zwei unsichtbare Eckpunkte erzwingen den Rand; gleicher Maßstab über scaleanchor nur mit automatischem Bereich
    fig.add_trace(go.Scatter(x=[min(xs_alle) - rand, max(xs_alle) + rand], y=[min(ys_alle) - rand, max(ys_alle) + rand], mode="markers", marker=dict(size=1, opacity=0),
                             hoverinfo="skip", showlegend=False))
    fig.update_xaxes(visible=False, fixedrange=True)
    fig.update_yaxes(visible=False, fixedrange=True, scaleanchor="x", scaleratio=1)
    fig.update_layout(height=hoehe, margin=dict(l=5, r=5, t=30, b=5), dragmode=False, plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)")
    return fig
