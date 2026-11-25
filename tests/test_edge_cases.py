"""Randfälle: Start mit Grad 1, Schwelle ohne Push, Netz mit zwei Plätzen, Menge mit mehr als halbem Volumen, unzusammenhängende Netze."""

import pytest

import lsn_netze as N
import lsn_sweep as W
from lsn_diffusion import ppr_exakt, push, waerme
from lsn_verfahren import ALLE, schnitt
from lsn_wachsen import GIERIG, gierig


def _zwei():
    return N.aus_kanten("zwei", 2, [(0, 1)])


def test_netz_mit_zwei_plaetzen_alle_verfahren():
    g = _zwei()
    for verfahren, par in (("pagerank", (0.25, 0.01)), ("pagerank-traege", (0.25, 0.01)), ("waerme", (1, 0.0)), ("bfs", 5)) + tuple((v, 5) for v in GIERIG):
        for regel in ("min", "tal0.4"):
            s = schnitt(g, {0}, 0, verfahren, par, regel)
            assert 1 <= s.ergebnis.groesse <= 2 and s.menge[0] == 0
    assert set(v for v, *_ in [(a,) for a in ALLE]) == set(ALLE)


def test_ein_platz_ohne_nachbarn():
    g = N.aus_kanten("einzeln", 3, [(1, 2)])
    p, r, z, pushes = push(g, 0, 0.3, 0.01)
    assert p == {} and r == {0: 1.0} and z == 0 and pushes == 0
    assert ppr_exakt(g, 0, 0.3).tolist() == [1.0, 0.0, 0.0]
    h, zz = waerme(g, 0, 3.0, 0.0)
    assert list(h) == [0] and zz == 0
    for art in GIERIG:
        reihe, _ = gierig(g, 0, 10, art)
        assert reihe == [0]
    s = schnitt(g, {0}, 0, "pagerank", (0.3, 0.01), "min")
    assert s.menge == (0,)


def test_start_mit_grad_eins():
    g = N.aus_kanten("Weg", 4, [(0, 1), (1, 2), (2, 3)])
    s = schnitt(g, {0, 1}, 0, "pagerank", (0.2, 1e-6), "min")
    assert set(s.menge) == {0, 1}                           # die mittlere Kante ist der kleinste Schnitt
    assert W.konduktanz(g, {0, 1}) == W.konduktanz(g, {2, 3})


def test_eps_so_gross_dass_kein_push_laeuft_gibt_den_start():
    g = N.handnetz()
    s = schnitt(g, N.ZIEL_HAND, 0, "pagerank", (0.2, 0.9), "min")
    assert s.menge == (0,) and s.ergebnis.zugriffe == g.d[0]            # nur der Sweep über den Start


def test_menge_mit_mehr_als_halbem_volumen():
    g = N.handnetz()
    assert W.konduktanz(g, {0, 1, 2, 3}) == W.konduktanz(g, {4, 5})


def test_budget_kleiner_als_der_start():
    g = N.handnetz()
    reihe, vols = gierig(g, 0, 1, "gierig-entdeckt")
    assert reihe == [0] and vols == [2]


def test_unzusammenhaengend_bleibt_in_der_komponente():
    g = N.aus_kanten("zwei Dreiecke", 6, [(0, 1), (1, 2), (0, 2), (3, 4), (4, 5), (3, 5)])
    p, *_ = push(g, 0, 0.1, 1e-4)
    assert set(p) == {0, 1, 2}
    assert ppr_exakt(g, 0, 0.1)[3:].sum() == pytest.approx(0.0, abs=1e-12)
    for art in GIERIG:
        reihe, _ = gierig(g, 0, 100, art)
        assert set(reihe) == {0, 1, 2}


def test_gemeinschaften_ohne_neuziehen_start_in_groesster_komponente():
    # kleine Gruppen: es gibt Plätze außerhalb der größten Komponente; der Start liegt trotzdem darin
    g, ziel, s = N.gemeinschaften(40, 4, 0.2, 3)
    gross = N.groesste_komponente(g)
    assert gross[s] and s in ziel and gross.sum() < g.n


def test_gleiche_werte_ordnet_die_nummer():
    g = N.aus_kanten("Stern", 4, [(0, 1), (0, 2), (0, 3)])
    assert W.reihe_nach(g, {1: 0.5, 2: 0.5, 3: 0.5, 0: 0.1}) == [1, 2, 3, 0]
    assert W.reihe_nach(g, {1: 0.0, 2: 0.2}) == [2]
