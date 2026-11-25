"""Gierige Erweiterung, Breitensuche, Gleichstandsbeispiel in der Gitterhalle."""

import pytest

import lsn_netze as N
from lsn_verfahren import schnitt
from lsn_wachsen import GIERIG, bfs_kugel, budget_laenge, gierig, start_laenge

ZIEL = N.ZIEL_HAND


@pytest.mark.parametrize("art", GIERIG)
def test_gierig_findet_auf_dem_handnetz_die_halle(hand, art):
    s = schnitt(hand, ZIEL, 0, art, 14, "min")
    assert sorted(s.menge) == [0, 1, 2] and s.ergebnis.f1 == 1.0


def test_gierig_reihenfolge_von_hand(hand):
    # ab 0 sind 1 und 2 Nachbarn; Anteil 1/2 (Grad 2) gegen 1/3 (Grad 3): zuerst Platz 1, danach Platz 2 mit 2/3
    reihe, vols = gierig(hand, 0, 14, "gierig-entdeckt")
    assert reihe[:3] == [0, 1, 2] and vols[:3] == [2, 4, 7]


def test_nachbarschafts_start_nimmt_alle_nachbarn_auch_ueber_das_budget(hand):
    reihe, vols = gierig(hand, 2, 3, "gierig-nachbar")
    assert sorted(reihe) == [0, 1, 2, 3] and vols[-1] == 10
    assert start_laenge(hand, 2, "gierig-nachbar") == 4
    assert budget_laenge(vols, 3, 4) == 4


def test_lauf_mit_kleinem_budget_ist_anfang_des_grossen():
    g = N.hallenverbund(3, 6)
    for art in GIERIG:
        s = sorted(N.mittlere_halle(3, 6))[7]
        gross, vols = gierig(g, s, 500, art)
        for budget in (40, 120, 300):
            klein, _ = gierig(g, s, budget, art)
            assert klein == gross[: budget_laenge(vols, budget, start_laenge(g, s, art))]


def test_gleichstandsregel_entscheidet_in_der_gitterhalle():
    # Handbeispiel: 3×3 Hallen zu 6×6, Start Platz (2,2) der mittleren Halle, erstes Tal 0,4
    g = N.hallenverbund(3, 6)
    ziel = N.mittlere_halle(3, 6)
    start = N.hallenknoten(3, 6, 1, 1, 2, 2)
    entdeckt = schnitt(g, ziel, start, "gierig-entdeckt", 400, "tal0.4")
    grad = schnitt(g, ziel, start, "gierig-grad", 400, "tal0.4")
    assert (entdeckt.ergebnis.groesse, len(set(entdeckt.menge) & ziel)) == (36, 36)
    assert (grad.ergebnis.groesse, len(set(grad.menge) & ziel)) == (54, 18)


def test_bfs_findet_auf_dem_handnetz_die_halle(hand):
    s = schnitt(hand, ZIEL, 0, "bfs", 14, "min")
    assert sorted(s.menge) == [0, 1, 2]


def test_bfs_ordnet_nach_abstand():
    g = N.hallenverbund(2, 5)
    reihe, vol = bfs_kugel(g, 0, 40)
    tiefen = [sum(divmod(u, 5)) for u in reihe]
    assert tiefen == sorted(tiefen) and vol >= 40
