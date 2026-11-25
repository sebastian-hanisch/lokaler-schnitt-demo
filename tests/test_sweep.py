"""Sweep, Konduktanz und Sweep-Regeln: Handrechnung auf dem Handnetz, Kontrastnetz mit Sammelpunkt, gebaute Kurven."""

from fractions import Fraction as Fr

import pytest

import lsn_sweep as W
from lsn_diffusion import push, ppr_exakt
from lsn_netze import ZIEL_HAND
from lsn_verfahren import schnitt


def test_konduktanz_treppe_nach_p_durch_grad(hand):
    p = {u: float(x) for u, x in enumerate(ppr_exakt(hand, 0, 0.25))}
    reihe = W.reihe_nach(hand, p)
    assert reihe == [0, 1, 2, 3, 4, 5]
    phis, vols = W.kurve(hand, reihe)
    assert phis[:5] == [1.0, 0.5, pytest.approx(1 / 7), 0.5, 1.0] and phis[5] == 2.0
    assert vols == [2, 4, 7, 10, 12, 14]
    assert W.waehle(phis, "min") == 3
    assert W.konduktanz(hand, {0, 1, 2}) == Fr(1, 7)


def test_ordnung_nach_p_allein(hand):
    p = {u: float(x) for u, x in enumerate(ppr_exakt(hand, 0, 0.25))}
    assert W.reihe_nach(hand, p, normiert=False) == [0, 2, 1, 3, 4, 5]


def test_push_sweep_findet_die_halle(hand):
    p, *_ = push(hand, 0, 0.25, 0.05)
    s = schnitt(hand, ZIEL_HAND, 0, "pagerank", (0.25, 0.05), "min")
    assert sorted(s.menge) == [0, 1, 2] and s.ergebnis.f1 == 1.0
    assert s.ergebnis.zugriffe == 19 + sum(hand.d[u] for u in p)       # Aufbau plus Sweep


def test_sammelpunkt_kommt_ohne_division_in_den_schnitt(sammel):
    p = ppr_exakt(sammel, 0, 0.25)
    soll = [Fr(60, 173), Fr(127, 865), Fr(121, 865), Fr(76, 865), Fr(48, 865), Fr(48, 865), Fr(29, 173)]
    assert max(abs(p[u] - float(soll[u])) for u in range(7)) < 1e-10
    werte = {u: float(p[u]) for u in range(7)}
    normiert = W.reihe_nach(sammel, werte)
    roh = W.reihe_nach(sammel, werte, normiert=False)
    assert roh[1] == 6 and normiert[:3] == [0, 1, 2]
    for reihe, menge, phi in ((normiert, {0, 1, 2}, Fr(1, 3)), (roh, {0, 1, 2, 6}, Fr(2, 5))):
        phis, _ = W.kurve(sammel, reihe)
        k = W.waehle(phis, "min")
        assert set(reihe[:k]) == menge and W.konduktanz(sammel, menge) == phi


def test_waehle_min_nimmt_das_erste_minimum():
    assert W.waehle([0.9, 0.4, 0.6, 0.4, 2.0], "min") == 2


def test_erstes_tal_haelt_nach_dem_anstieg():
    #        k:   1    2    3    4    5    6    7    8    9
    phis = [1.0, 0.5, 0.4, 0.35, 0.30, 0.20, 0.30, 0.10, 0.05]
    assert W.waehle(phis, "tal0.4") == 6          # 0,30 > 0,20·1,4
    assert W.waehle(phis, "tal0.8") == 9          # kein Anstieg um 80 %: das kleinste insgesamt
    assert W.waehle(phis, "min") == 9


def test_erstes_tal_zaehlt_erst_ab_fuenf_plaetzen():
    phis = [0.01, 0.9, 0.9, 0.9, 0.5, 0.9]
    assert W.waehle(phis, "tal0.4") == 5
    assert W.waehle(phis, "min") == 1


def test_waehle_ohne_gueltigen_nenner():
    assert W.waehle([2.0], "min") == 1


def test_waehle_nur_im_praefix():
    assert W.waehle([0.9, 0.5, 0.1], "min", laenge=2) == 2


def test_regel_namen():
    assert W.regel_name(None) == "min" and W.regel_name(0.4) == "tal0.4" and W.regel_gamma("tal0.02") == 0.02
    with pytest.raises(ValueError):
        W.regel_gamma("nichts")


def test_f1():
    assert W.f1(3, 3, 3) == 1.0
    assert W.f1(2, 4, 4) == 0.5
    assert W.f1_menge({1, 2, 3}, {3, 4}) == pytest.approx(0.4)
    assert W.f1(0, 0, 0) == 0.0


def test_konduktanz_ohne_gegenueber_ist_fehler(hand):
    with pytest.raises(ValueError):
        W.konduktanz(hand, range(6))
