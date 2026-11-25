"""Netzerzeuger: Handnetze, Hallenverbund (Brüche des Handbeispiels), Zufallsgemeinschaften und Sammelpunkte."""

import networkx as nx
import pytest

import lsn_netze as N
from lsn_sweep import konduktanz
from fractions import Fraction


def _symmetrisch(g):
    for u in range(g.n):
        assert g.nb[u] == sorted(set(g.nb[u])) and u not in g.nb[u]
        assert all(u in g.nb[v] for v in g.nb[u])
    assert g.d == [len(x) for x in g.nb] and g.vol == sum(g.d)


def test_handnetz_und_sammelpunkt(hand, sammel):
    assert hand.d == [2, 2, 3, 3, 2, 2] and hand.vol == 14
    assert sammel.d == [3, 3, 3, 4, 3, 3, 5] and sorted(sammel.nb[6]) == [0, 1, 3, 4, 5]
    _symmetrisch(hand)
    _symmetrisch(sammel)


def test_aus_kanten_weist_fehler_ab():
    for kanten in ([(0, 0)], [(0, 3)], [(0, 1), (1, 0)]):
        with pytest.raises(ValueError):
            N.aus_kanten("x", 3, kanten)


def test_hallenverbund_kanten_und_volumen():
    g = N.hallenverbund(8, 8)
    _symmetrisch(g)
    assert g.n == 4096
    # je Halle 2·a·(a−1) = 112 Kanten, dazu 2·8·7 = 112 Türen
    assert g.m == 64 * 112 + 112


@pytest.mark.parametrize("zeilen, spalten, soll", [(1, 1, Fraction(4, 228)), (1, 2, Fraction(6, 456)), (2, 2, Fraction(8, 912))])
def test_konduktanz_treppe_aus_dem_handbeispiel(zeilen, spalten, soll):
    g = N.hallenverbund(8, 8)
    block = N.block_plaetze(8, 8, zeilen, spalten)
    assert N.mittlere_halle(8, 8) <= block
    assert konduktanz(g, block) == soll
    G = nx.Graph(N.kanten_von(g))
    assert nx.conductance(G, block) == pytest.approx(float(soll), abs=1e-12)


def test_hallenverbund_ist_zweiteilig():
    for z, a in ((3, 5), (4, 6), (3, 8)):
        G = nx.Graph(N.kanten_von(N.hallenverbund(z, a)))
        assert nx.is_bipartite(G) and nx.is_connected(G)


def test_gemeinschaften_reproduzierbar_und_zielgruppe():
    a = N.gemeinschaften(960, 60, 1.0, 12345)
    b = N.gemeinschaften(960, 60, 1.0, 12345)
    c = N.gemeinschaften(960, 60, 1.0, 12346)
    assert a[0].nb == b[0].nb and a[2] == b[2]
    assert a[0].nb != c[0].nb
    g, ziel, s = a
    _symmetrisch(g)
    assert ziel == frozenset(range(60)) and s in ziel and g.n == 960
    G = nx.Graph(N.kanten_von(g))
    assert s in max(nx.connected_components(G), key=len)


def test_gemeinschaften_mittlere_grade():
    # erwartet: 8 Nachbarn in der Gruppe, 1 bzw. 3 nach außen (bis auf entfallene Paare); Band aus der Stichprobe
    for aussen in (1.0, 3.0):
        g, _, _ = N.gemeinschaften(16000, 60, aussen, 99)
        innen = sum(1 for u in range(g.n) for v in g.nb[u] if u // 60 == v // 60) / g.n
        aus = sum(g.d) / g.n - innen
        assert abs(innen - 8) < 0.15
        assert abs(aus - aussen * (1 - 1 / (16000 // 60))) < 0.1


def test_gemeinschaften_rundet_n_ab_und_prueft_eingaben():
    g, _, _ = N.gemeinschaften(1000, 60, 1.0, 1)
    assert g.n == 960
    with pytest.raises(ValueError):
        N.gemeinschaften(100, 60, 1.0, 1)


def test_sammelpunkte_haengen_wie_beschrieben():
    g, ziel, s, sammel = N.mit_sammelpunkten(1920, 60, 7, 5, 12, 300)
    grund, _, s2 = N.gemeinschaften(1920, 60, 1.0, 7)
    assert s == s2 and len(sammel) == 5 and g.n == grund.n + 5
    for h in sammel:
        assert g.d[h] == 312
        assert sum(v in ziel for v in g.nb[h]) == 12
    _symmetrisch(g)
    # ohne Sammelpunkte ist es dasselbe Grundnetz
    assert N.mit_sammelpunkten(1920, 60, 7, 0, 0, 0)[0].nb == grund.nb
    fern = N.mit_sammelpunkten(1920, 60, 7, 3, 0, 100)
    assert all(fern[0].d[h] == 100 for h in fern[3])


def test_hallen_koordinaten_und_namen_sind_eindeutig():
    z, a = 3, 4
    punkte = {N.hallen_koordinate(z, a, u) for u in range(z * z * a * a)}
    assert len(punkte) == z * z * a * a
    assert N.hallen_name(z, a, 0) == "Halle (0,0), Platz (0,0)"
    assert N.hallen_name(z, a, N.hallenknoten(z, a, 2, 1, 3, 2)) == "Halle (2,1), Platz (3,2)"
