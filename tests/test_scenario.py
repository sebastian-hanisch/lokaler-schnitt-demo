"""Szenarien: Zielmenge, Startplatz, Familie und Kartenausschnitt je Netzart."""

import pytest

import lsn_constants as C
import lsn_netze as N
import lsn_scenario as S


def test_handnetze():
    s = S.baue(C.NETZ_HAND, start_platz=2)
    assert s.start == 2 and s.ziel == N.ZIEL_HAND and s.familie is None and s.hat_karte
    t = S.baue(C.NETZ_SAMMEL)
    assert t.sammel == frozenset({6}) and t.g.n == 7 and "Sammelpunkt" in t.platz_name(6)


@pytest.mark.parametrize("wahl", C.HALLEN_STARTS)
def test_hallen_start_liegt_in_der_mittleren_halle(wahl):
    for z, a in ((4, 4), (8, 12)):
        s = S.baue(C.NETZ_HALLEN, a=a, z=z, start_halle=wahl, seed=5)
        assert s.start in s.ziel and len(s.ziel) == a * a and s.familie == "hallen" and s.z == z and s.a == a


def test_hallen_ecke_und_tuer():
    s = S.baue(C.NETZ_HALLEN, a=8, z=8, start_halle="ecke")
    assert N.hallen_name(8, 8, s.start) == "Halle (4,4), Platz (0,0)"
    t = S.baue(C.NETZ_HALLEN, a=8, z=8, start_halle="tuer")
    assert N.hallen_name(8, 8, t.start) == "Halle (4,4), Platz (4,0)" and t.g.d[t.start] == 4
    with pytest.raises(ValueError):
        S.hallen_startplatz(8, 8, "nichts", 1)


def test_zufallshallen_start_haengt_am_seed():
    starts = {S.baue(C.NETZ_HALLEN, a=8, z=4, start_halle="zufall", seed=k).start for k in range(20)}
    assert len(starts) > 5


def test_gemeinschaften_und_sammelpunkte():
    s = S.baue(C.NETZ_GEMEIN, n=4000, groesse=60, aussen=3, seed=11)
    assert s.familie == "a3" and len(s.ziel) == 60 and s.g.n == 3960 and not s.hat_karte
    t = S.baue(C.NETZ_NADELN, n=4000, sammelart="fern40", seed=11)
    assert len(t.sammel) == 40 and t.familie == "a1" and all(t.g.d[h] == 400 for h in t.sammel)
    with pytest.raises(ValueError):
        S.baue("nichts")


def test_mindestens_zwei_gruppen():
    assert S.plaetze_gewirkt(960, 960) == 1920 and S.plaetze_gewirkt(960, 60) == 960
    s = S.baue(C.NETZ_GEMEIN, n=960, groesse=960, aussen=3, seed=2)
    assert s.g.n == 1920


def test_ausschnitt():
    s = S.baue(C.NETZ_HALLEN, a=4, z=8)
    knoten = S.ausschnitt(s)
    assert len(knoten) == 9 * 16 and set(s.ziel) <= set(knoten)
    assert len(S.ausschnitt(S.baue(C.NETZ_HAND))) == 6
