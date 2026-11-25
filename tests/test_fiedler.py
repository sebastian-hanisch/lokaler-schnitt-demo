"""Globaler Fiedler-Sweep: auf einem Netz mit eindeutiger Zweiteilung findet er sie; die Eigenwerte stimmen mit der dichten Zerlegung überein."""

import numpy as np
import pytest

import lsn_netze as N
from lsn_fiedler import fiedler_sweep


def _zwei_cliquen(k=8):
    kanten = [(i, j) for i in range(k) for j in range(i + 1, k)] + [(k + i, k + j) for i in range(k) for j in range(i + 1, k)] + [(0, k)]
    return N.aus_kanten("zwei Cliquen", 2 * k, kanten)


def test_findet_die_eindeutige_zweiteilung():
    g = _zwei_cliquen()
    r = fiedler_sweep(g, set(range(8)))
    assert r["groesse"] == 8 and r["f1"] in (1.0, 0.0)           # eine der beiden Cliquen (gleiche Konduktanz)
    assert r["konduktanz"] == pytest.approx(1 / 57)


def test_eigenwertabstand_gegen_dichte_zerlegung():
    g, ziel, _ = N.gemeinschaften(300, 60, 1.0, 4)
    A = np.zeros((g.n, g.n))
    for u in range(g.n):
        A[u, g.nb[u]] = 1
    w = 1 / np.sqrt(np.maximum(A.sum(1), 1))
    werte = np.sort(np.linalg.eigvalsh(w[:, None] * A * w[None, :] + np.eye(g.n)))[::-1]
    r = fiedler_sweep(g, ziel)
    assert r["abstand_ew"] == pytest.approx(werte[1] - werte[2], abs=1e-6)
