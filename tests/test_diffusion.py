"""Push und Wärmeleitung gegen die Handrechnung auf dem Handnetz (Brüche aus dem Handbeispiel)."""

from fractions import Fraction as Fr

import numpy as np
import pytest

from lsn_diffusion import ppr_exakt, push, waerme, waerme_gewichte

PPR_HAND = [Fr(244, 627), Fr(130, 627), Fr(14, 57), Fr(5, 57), Fr(2, 57), Fr(2, 57)]


def _vektor(w, n):
    return np.array([w.get(i, 0.0) for i in range(n)])


def test_ppr_exakt_ist_der_bruch_aus_der_handrechnung(hand):
    p = ppr_exakt(hand, 0, 0.25)
    assert np.allclose(p, [float(x) for x in PPR_HAND], atol=1e-12)
    assert p[:3].sum() == pytest.approx(16 / 19, abs=1e-12)
    assert p[2] > p[1] and p[2] / 3 < p[1] / 2          # Platz 2 hat mehr PageRank als 1, je Nachbar weniger


def test_push_von_hand(hand):
    protokoll = []
    p, r, z, pushes = push(hand, 0, 0.25, 0.05, protokoll=protokoll)
    assert [x[0] for x in protokoll] == [0, 1, 2, 0, 1, 2, 0, 3]
    assert pushes == 8 and z == 19 and z == sum(hand.d[u] for u, *_ in protokoll)
    assert [protokoll[i][1] for i in range(4)] == [1.0, 3 / 8, 33 / 64, 69 / 256]
    soll = [Fr(91921, 262144), Fr(1239, 8192), Fr(11517, 65536), Fr(11517, 262144), 0, 0]
    assert np.array_equal(_vektor(p, 6), [float(x) for x in soll])      # alle Brüche haben Zweierpotenz-Nenner
    assert _vektor(p, 6).sum() + _vektor(r, 6).sum() == 1.0
    assert z <= 1 / (0.25 * 0.05)


def test_push_invariante_nach_jedem_schritt(hand):
    protokoll = []
    push(hand, 0, 0.25, 0.05, protokoll=protokoll)
    voll = ppr_exakt(hand, 0, 0.25)
    for _, _, p, r in protokoll:
        rest = sum(r.get(v, 0) * ppr_exakt(hand, v, 0.25) for v in range(6))
        assert np.allclose(_vektor(p, 6) + rest, voll, atol=1e-10)


def test_traege_fassung_mit_alpha_ein_siebtel(hand):
    # dieselbe Zielgröße: mit sehr kleinem ε liegen beide Näherungen am exakten Wert
    p, _, _, _ = push(hand, 0, 0.25, 1e-9, traege=True)
    assert np.allclose(_vektor(p, 6), [float(x) for x in PPR_HAND], atol=1e-7)


def test_push_ohne_schritt_wenn_eps_zu_gross(hand):
    p, r, z, pushes = push(hand, 0, 0.25, 0.6)
    assert p == {} and r == {0: 1.0} and z == 0 and pushes == 0


def test_push_prueft_die_parameter(hand):
    for beta, eps in ((0.0, 0.1), (1.0, 0.1), (0.3, 0.0)):
        with pytest.raises(ValueError):
            push(hand, 0, beta, eps)


def test_waerme_gewichte_rest():
    for t in (1.0, 10.0, 80.0):
        w = waerme_gewichte(t)
        assert 1 - sum(w) <= 1e-3 < 1 - sum(w[:-1])


def test_waerme_ohne_abschneiden_ist_die_reihe(hand):
    h, z = waerme(hand, 0, 1.0, 0.0)
    P = np.zeros((6, 6))
    for u in range(6):
        P[u, hand.nb[u]] = 1 / hand.d[u]
    x, soll, g = np.eye(6)[0], np.zeros(6), np.exp(-1.0)
    for k in range(len(waerme_gewichte(1.0))):
        soll += g * x
        x = x @ P
        g /= k + 1
    assert np.allclose(_vektor(h, 6), soll, atol=1e-12)
    assert z > 0


def test_waerme_mit_grosser_schwelle_bleibt_am_start(hand):
    h, z = waerme(hand, 0, 5.0, 10.0)
    assert list(h) == [0] and z == 0
