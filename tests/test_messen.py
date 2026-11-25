"""Messdefinitionen: feste, sich nicht überschneidende Zufalls-Seeds, Fallzahlen, Auswahlregel an gesetzten Werten und Gleichheit der Sammelläufe mit Einzelläufen."""

import pytest

import lsn_messen as M
import lsn_netze as N
from lsn_verfahren import Ergebnis, kennzahlen, laufe, median, schnitt


def test_seed_bereiche_ueberschneiden_sich_nicht():
    gesehen = set()
    for reihe in M.BASIS:
        bereich = range(M.seed_von(reihe), M.seed_von(reihe) + 10 ** 7)
        assert not gesehen & {bereich.start, bereich.stop - 1}
        gesehen |= {bereich.start, bereich.stop - 1}
    werte = [M.seed_von(r, a, g, i) for r in ("abst", "test") for a in (1, 3) for g in M.GROESSEN_TEST for i in range(M.NETZE_TEST)]
    assert len(set(werte)) == len(werte)
    n_seeds = [M.seed_von("n_reihe") + n * 100 + i for n in M.N_REIHE for i in range(M.N_REIHE_NETZE)]
    assert len(set(n_seeds)) == len(n_seeds) and max(n_seeds) < M.seed_von("sammel_nah")


def test_fallzahlen():
    assert len(list(M.abstimm_faelle("hallen"))) == 4 * 16
    assert len(list(M.abstimm_faelle("a1"))) == 5 * 8
    assert sum(1 for _ in M.test_faelle("hallen")) == 36 + 64 + 100 + 144 + 256 + 400 == 1000
    assert sum(1 for _ in M.test_faelle("a3")) == 7 * 60


def test_abstimm_starts_der_hallen_sind_verschieden_und_in_der_halle():
    for a, i, bau in M.abstimm_faelle("hallen"):
        netz, ziel, s = bau()
        assert s in ziel and netz.n == 36 * a * a
        if i == 15:
            break


def test_raster_groessen():
    assert len(M.raster("pagerank")) == 6 * 8 * 8
    assert len(M.raster("waerme")) == 5 * 5 * 8
    assert len(M.raster("gierig")) == (3 * 13 + 8) * 8


def test_gemeinsamer_lauf_gleich_einzellauf():
    netz, ziel, s = N.gemeinschaften(1920, 60, 1.0, 17)
    keys = [("pagerank", (0.006, 3e-4), r) for r in ("min", "tal0.1")] + [("gierig-nachbar", B, "tal0.2") for B in (300, 1000, 3300)]
    keys += [("gierig-grad", 600, "min"), ("waerme", (5, 3e-4), "min"), ("bfs", 600, "tal0.4"), ("pagerank-traege", (0.006, 3e-4), "min")]
    gemeinsam = laufe(netz, ziel, s, keys)
    for k in keys:
        einzeln = schnitt(netz, ziel, s, *k).ergebnis
        assert gemeinsam[k] == einzeln, k


def test_auswahlregel_nimmt_unter_gleich_guten_die_sparsamste():
    # eine Zelle, zwei Netze; gesetzte Ergebnisse
    keys = [(v, p, r) for v in M.VERFAHREN_VERGLEICH for p in (100, 200) for r in ("min", "tal0.4")]
    lauf = {k: Ergebnis(0.5, 1000, 10) for k in keys}
    lauf[("pagerank", 100, "min")] = Ergebnis(0.900, 5000, 10)
    lauf[("pagerank", 200, "min")] = Ergebnis(0.896, 300, 10)          # innerhalb 0,005, aber sparsamer
    lauf[("pagerank", 100, "tal0.4")] = Ergebnis(0.90, 100, 10)
    lauf[("pagerank", 200, "tal0.4")] = Ergebnis(0.894, 1, 10)         # 0,006 darunter: nicht
    ergebnisse = {(7, 0): lauf, (7, 1): lauf}
    import lsn_messen
    alt = lsn_messen.am_rand
    lsn_messen.am_rand = lambda v, p: []
    try:
        w = M.waehle_einstellungen(ergebnisse, (7,))
    finally:
        lsn_messen.am_rand = alt
    assert w["pagerank"]["min"]["par"] == 200 and w["pagerank"]["tal"]["par"] == 100
    assert w["pagerank"]["min"]["abst_mittel"] == pytest.approx(0.896)
    assert w["pagerank"]["min"]["abst_hoechstwert"] == pytest.approx(0.9)
    assert M.haupt_sweep(w, "pagerank") == "tal"


def test_am_rand():
    assert M.am_rand("pagerank", (0.00075, 3e-4)) == ["beta"] and M.am_rand("pagerank", (0.006, 1e-3)) == ["eps"]
    assert M.am_rand("waerme", (80, 3e-5)) == ["t"] and M.am_rand("gierig-nachbar", 28000) == ["B"] and M.am_rand("bfs", 600) == []


def test_median_und_kennzahlen():
    assert median([3, 1, 2]) == 2 and median([4, 1, 3, 2]) == 2.5
    k = kennzahlen([Ergebnis(0.9, 10, 3), Ergebnis(0.89, 30, 5), Ergebnis(1.0, 20, 4)])
    assert k == {"median": 0.9, "mittel": pytest.approx((0.9 + 0.89 + 1.0) / 3), "treffer": 2, "zahl": 3, "zugriffe": 20, "groesse": 4}
