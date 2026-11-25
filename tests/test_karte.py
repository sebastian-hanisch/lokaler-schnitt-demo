"""Karte: Punkte, Auswahl-Deckkraft, gesperrte Achsen, Ausschnitt großer Netze."""

import lsn_netze as N
from lsn_karte import GROSS_AB, karte


def test_karte_handnetz(hand):
    fig = karte(hand, N.HAND_POS, marken={0: ("s", "#000000")})
    punkte = fig.data[1]
    assert list(punkte.customdata) == [0, 1, 2, 3, 4, 5]
    assert punkte.selected.marker.opacity == 1 and punkte.unselected.marker.opacity == 1
    assert fig.layout.xaxis.fixedrange and fig.layout.yaxis.fixedrange and fig.layout.dragmode is False
    beschriftungen = [a.text for a in fig.layout.annotations]
    assert beschriftungen[:6] == ["0", "1", "2", "3", "4", "5"] and "<b>s</b>" in beschriftungen


def test_karte_ausschnitt_zeichnet_nur_die_gewaehlten_knoten_und_kanten():
    g = N.hallenverbund(4, 4)
    pos = [N.hallen_koordinate(4, 4, u) for u in range(g.n)]
    knoten = list(N.halle_plaetze(4, 4, 1, 1))
    fig = karte(g, pos, knoten=knoten, werte=[float(u) for u in range(g.n)], farbtitel="Wert")
    assert list(fig.data[1].customdata) == knoten and len(fig.data[1].x) == 16
    assert len(fig.data[0].x) == 3 * 24          # 2·4·3 = 24 Kanten in der Halle, Türen nach außen fallen weg


def test_grosse_ausschnitte_mit_webgl():
    g = N.hallenverbund(3, 24)
    pos = [N.hallen_koordinate(3, 24, u) for u in range(g.n)]
    assert g.n > GROSS_AB
    assert karte(g, pos).data[1].type == "scattergl"
