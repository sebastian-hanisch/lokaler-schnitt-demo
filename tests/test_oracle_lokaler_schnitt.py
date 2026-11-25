"""Orakel: jede Kerngröße gegen einen unabhängigen Rechenweg auf zufälligen kleinen Netzen.

* Push gegen dichtes Gleichungssystem (Invariante p + ppr(r) = ppr(s), Fehlerschranke 0 ≤ ppr − p ≤ ε·Grad) und gegen `networkx.pagerank` (alpha = 1 − β);
  die träge Fassung gegen die träge Gleichung.
* `ppr_exakt` (konjugierte Gradienten) gegen `numpy.linalg.solve`.
* Wärmeleitung ohne Abschneiden gegen `scipy.linalg.expm`.
* Sweep (fortlaufend gezählt) gegen Neuzählung je Anfangsstück und `networkx.conductance`.
* Gierige Erweiterung (Haufen) gegen eine Zweitfassung, die je Schritt alle Randplätze neu bewertet, mit exakten Brüchen.
* Kantenzugriffe gegen Nachzählen des Protokolls."""

from fractions import Fraction

import networkx as nx
import numpy as np
import pytest
from scipy.linalg import expm

import lsn_netze as N
import lsn_sweep as W
from conftest import zufallsnetz
from lsn_diffusion import ppr_exakt, push, waerme
from lsn_wachsen import GIERIG, gierig
from lsn_zufall import BlockZufall

NETZE = range(40)


def _P(g):
    P = np.zeros((g.n, g.n))
    for u in range(g.n):
        P[u, g.nb[u]] = 1 / g.d[u]
    return P


def _zufallswerte(seed):
    r = BlockZufall(seed + 500)
    g = zufallsnetz(seed, 4, 24)
    s = r.unter(g.n)
    beta = 0.02 + 0.48 * r.unter(1000) / 1000
    eps = 10 ** (-4 + 2.5 * r.unter(1000) / 1000)
    return g, s, beta, eps, r


@pytest.mark.parametrize("seed", NETZE)
def test_push_gegen_dichtes_gleichungssystem(seed):
    g, s, beta, eps, _ = _zufallswerte(seed)
    P = _P(g)
    voll_von = beta * np.linalg.solve(np.eye(g.n) - (1 - beta) * P, np.eye(g.n))          # Zeile v: ppr ab v
    for traege in (False, True):
        protokoll = []
        p, r, z, pushes = push(g, s, beta, eps, traege=traege, protokoll=protokoll)
        pv = np.array([p.get(u, 0.0) for u in range(g.n)])
        rv = np.array([r.get(u, 0.0) for u in range(g.n)])
        assert np.abs(pv + rv @ voll_von - voll_von[s]).max() < 1e-10                      # Invariante
        diff = voll_von[s] - pv
        assert diff.min() > -1e-10 and (diff - eps * np.array(g.d)).max() < 1e-10          # Fehlerschranke
        assert rv.max(initial=0) < (eps * np.array(g.d)).max() + 1e-15
        assert all(r.get(u, 0.0) < eps * g.d[u] for u in range(g.n))
        assert z == sum(g.d[u] for u, *_ in protokoll) and pushes == len(protokoll)
        rate = beta / (2 - beta) if traege else beta
        assert z <= 1 / (rate * eps) + 1e-9
        assert abs(pv.sum() + rv.sum() - 1) < 1e-10


@pytest.mark.parametrize("seed", NETZE)
def test_ppr_exakt_gegen_numpy_und_networkx(seed):
    g, s, beta, _, _ = _zufallswerte(seed)
    voll = beta * np.linalg.solve((np.eye(g.n) - (1 - beta) * _P(g)).T, np.eye(g.n)[s])
    assert np.abs(ppr_exakt(g, s, beta) - voll).max() < 1e-9
    nxp = nx.pagerank(nx.Graph(N.kanten_von(g)), alpha=1 - beta, personalization={s: 1}, tol=1e-13, max_iter=10000)
    assert max(abs(nxp[u] - voll[u]) for u in range(g.n)) < 1e-8


@pytest.mark.parametrize("seed", NETZE)
def test_traege_gleichung_hat_dieselbe_zielgroesse(seed):
    g, s, beta, _, _ = _zufallswerte(seed)
    alpha = beta / (2 - beta)
    W2 = 0.5 * (np.eye(g.n) + _P(g))
    traege = alpha * np.linalg.solve((np.eye(g.n) - (1 - alpha) * W2).T, np.eye(g.n)[s])
    assert np.abs(traege - ppr_exakt(g, s, beta)).max() < 1e-9


@pytest.mark.parametrize("seed", NETZE)
def test_waerme_ohne_abschneiden_gegen_expm(seed):
    g, s, _, _, r = _zufallswerte(seed)
    t = 0.5 + r.unter(800) / 100
    h, _ = waerme(g, s, t, 0.0)
    hv = np.array([h.get(u, 0.0) for u in range(g.n)])
    soll = expm(-t * (np.eye(g.n) - _P(g)))[s]
    assert np.abs(hv - soll).sum() <= 1e-3 + 1e-9                  # Rest der Reihe
    assert 0.999 - 1e-9 <= hv.sum() <= 1 + 1e-12


@pytest.mark.parametrize("seed", NETZE)
def test_sweep_gegen_neuzaehlung(seed):
    g, _, _, _, r = _zufallswerte(seed)
    reihe = r.mischen(np.arange(g.n)).tolist()[: 1 + r.unter(g.n)]
    phis, vols = W.kurve(g, reihe)
    G = nx.Graph(N.kanten_von(g))
    for k in range(1, len(reihe) + 1):
        menge = reihe[:k]
        assert vols[k - 1] == sum(g.d[u] for u in menge)
        if 0 < vols[k - 1] < g.vol:
            rand = nx.cut_size(G, menge)
            assert phis[k - 1] == pytest.approx(rand / min(vols[k - 1], g.vol - vols[k - 1]), abs=1e-12)
            assert phis[k - 1] == pytest.approx(nx.conductance(G, menge), abs=1e-12)
            assert float(W.konduktanz(g, menge)) == pytest.approx(phis[k - 1], abs=1e-12)
        else:
            assert phis[k - 1] == 2.0
    # die Regel min nimmt das erste kleinste
    k = W.waehle(phis, "min")
    assert phis[k - 1] <= min(phis) + 1e-12
    assert all(f > phis[k - 1] for f in phis[: k - 1])


def _gierig_schlicht(g, s, budget, art):
    drin = {s}
    reihe = [s]
    entdeckt = [s] + list(g.nb[s])
    if art == "gierig-nachbar":
        for v in g.nb[s]:
            drin.add(v)
            reihe.append(v)
            entdeckt += [x for x in g.nb[v] if x not in entdeckt]
    while sum(g.d[u] for u in drin) < budget:
        rand = sorted({v for u in drin for v in g.nb[u]} - drin)
        if not rand:
            break

        def schluessel(v):
            anteil = Fraction(sum(x in drin for x in g.nb[v]), g.d[v])
            return (-anteil, g.d[v], v) if art == "gierig-grad" else (-anteil, entdeckt.index(v))

        u = min(rand, key=schluessel)
        drin.add(u)
        reihe.append(u)
        entdeckt += [x for x in g.nb[u] if x not in entdeckt]
    return reihe


@pytest.mark.parametrize("art", GIERIG)
@pytest.mark.parametrize("seed", range(20))
def test_gierig_gegen_zweitfassung(seed, art):
    g, s, _, _, r = _zufallswerte(seed)
    budget = 1 + r.unter(g.vol + 3)
    reihe, vols = gierig(g, s, budget, art)
    assert reihe == _gierig_schlicht(g, s, budget, art)
    assert vols == list(np.cumsum([g.d[u] for u in reihe]))
