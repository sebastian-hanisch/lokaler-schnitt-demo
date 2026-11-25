"""Auf den zwei Handnetzen ist die gepflanzte Menge die Halle, in der der Start liegt. Geprüft für jeden wählbaren Startplatz beider Netze: am Szenario, über ein
Raster der Einstellungen und am angezeigten Text. Zweiter Rechenweg: das dichte Gleichungssystem mit numpy und F1 aus den Mengen."""

import itertools
import re
from pathlib import Path

import numpy as np
import pytest
from streamlit.testing.v1 import AppTest

import lsn_constants as C
import lsn_scenario as S
from lsn_verfahren import schnitt

APP = str(Path(__file__).resolve().parent.parent / "app.py")
NETZE = (C.NETZ_HAND, C.NETZ_SAMMEL)
STARTS = range(6)


def _halle(start):
    return {0, 1, 2} if start in (0, 1, 2) else {3, 4, 5}


def _anteil_dicht(g, start, beta):
    """p = β e_s + (1 − β) p P als dichtes System; Anteil in der Halle des Starts."""
    P = np.zeros((g.n, g.n))
    for u in range(g.n):
        for v in g.nb[u]:
            P[u, v] = 1 / g.d[u]
    e = np.zeros(g.n)
    e[start] = beta
    p = np.linalg.solve((np.eye(g.n) - (1 - beta) * P).T, e)
    return float(sum(p[u] for u in _halle(start)))


def _komma(x, stellen):
    return f"{x:.{stellen}f}".replace(".", ",")


def test_jeder_wählbare_start_gehoert_zu_seiner_zielhalle():
    for netz, start in itertools.product(NETZE, STARTS):
        sz = S.baue(netz, start_platz=start)
        assert set(sz.ziel) == _halle(start) and sz.start == start and start in sz.ziel and 6 not in sz.ziel, (netz, start)


@pytest.mark.parametrize("netz", NETZE)
def test_ein_start_ohne_halle_wird_abgewiesen(netz):
    with pytest.raises(ValueError):
        S.baue(netz, start_platz=6)


@pytest.mark.parametrize("netz", NETZE)
def test_f1_ueber_das_raster_der_einstellungen_gegen_die_halle_des_starts(netz):
    regeln = ("min",) + tuple(f"tal{g:g}" for g in C.GAMMA_STUFEN)
    for start in STARTS:
        sz = S.baue(netz, start_platz=start)
        faelle = [("pagerank", (b, e)) for b in C.BETA_STUFEN for e in C.EPS_STUFEN]
        faelle += [(art, b) for art in C.GIERIG_TEXT for b in C.BUDGET_STUFEN]
        faelle += [("waerme", (3, 0.0)), ("bfs", sz.g.vol)]
        for (verfahren, par), regel in itertools.product(faelle, regeln):
            s = schnitt(sz.g, sz.ziel, sz.start, verfahren, par, regel)
            menge = set(s.menge)
            f1 = 2 * len(menge & _halle(start)) / (len(menge) + 3)
            assert s.ergebnis.f1 == pytest.approx(f1), (netz, start, verfahren, par, regel)


@pytest.mark.parametrize("netz", NETZE)
@pytest.mark.parametrize("start", STARTS)
@pytest.mark.parametrize("beta, eps, regel", [(0.25, 0.05, "min"), (0.006, 3e-4, "tal")])
def test_angezeigte_texte_beziehen_sich_auf_die_starthalle(netz, start, beta, eps, regel):
    at = AppTest.from_file(APP, default_timeout=300)
    for k, v in {"netz": netz, "start": start, "beta": beta, "eps": eps, "regel": regel}.items():
        at.query_params[k] = str(v)
    at.run()
    assert not at.exception and not at.error
    sz = S.baue(netz, start_platz=start)
    texte = [m.value for art in ("success", "info", "warning") for m in getattr(at, art)]
    anteile = [re.search(r"\*\*([0-9,]+) %\*\* des PageRank in der Starthalle", t) for t in texte]
    anteile = [m.group(1) for m in anteile if m]
    assert anteile == [_komma(100 * _anteil_dicht(sz.g, start, beta), 1)] * 2, (netz, start, anteile)      # Kernfrage 1 und Experiment 1
    s = schnitt(sz.g, sz.ziel, start, "pagerank", (beta, eps), "min" if regel == "min" else "tal0.4")
    menge = set(s.menge)
    f1 = 2 * len(menge & _halle(start)) / (len(menge) + 3)
    assert at.metric[1].value == _komma(f1, 2)
    befund = next(t for t in texte if t.startswith("PageRank (Push) mit Sweep findet"))
    assert f"F1 = {_komma(f1, 2)}" in befund and ("Treffer (F1 ≥ 0,9)" in befund) == (f1 >= 0.9)
    if menge == _halle(start):
        assert "andere Plätze" not in befund
    if len(menge) == 1:
        assert "findet 1 Platz (" in befund
    assert not any(re.search(r"(?<![0-9 ])1 (Plätze|Pushes|Kantenzugriffe)", t.replace("*", "")) for t in texte + [m.value for m in at.markdown])


def test_gemeldeter_fall_start_am_anderen_ende_der_tuer():
    at = AppTest.from_file(APP, default_timeout=300)
    for k, v in {"netz": "hand", "start": 3, "beta": 0.25, "eps": 0.05, "regel": "min"}.items():
        at.query_params[k] = str(v)
    at.run()
    texte = [m.value for art in ("success", "info", "warning") for m in getattr(at, art)]
    assert any("**73,7 %** des PageRank in der Starthalle" in t for t in texte)
    assert at.metric[1].value == "1,00"
    assert any(t.startswith("PageRank (Push) mit Sweep findet 3 Plätze") and "Treffer (F1 ≥ 0,9)" in t for t in texte)


def test_hilfetext_und_ueberblick_nennen_die_halle_des_starts():
    at = AppTest.from_file(APP, default_timeout=300)
    at.run()
    hilfe = at.sidebar.selectbox(key="start_platz").help
    assert "in der der Start liegt" in hilfe and "Sammelpunkt 6 gehört zu keiner Halle" in hilfe
    assert any("der Sammelpunkt 6 gehört zu keiner Halle" in m.value for m in at.markdown)
