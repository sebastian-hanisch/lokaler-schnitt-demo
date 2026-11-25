"""Gemeinsame Test-Hilfen: Importpfad zum Demo-Ordner, Handnetze und zufällige kleine Netze für Orakel und Eigenschaften."""

import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import lsn_netze as N  # noqa: E402
from lsn_zufall import BlockZufall  # noqa: E402


def zufallsnetz(seed: int, n_min: int = 4, n_max: int = 24, zusammenhaengend: bool = True) -> N.Graph:
    """Zufälliges kleines Netz: ein zufälliger Baum (falls zusammenhängend gewünscht) plus zufällige Zusatzkanten; ohne Neuziehen bis zum Zusammenhang."""
    r = BlockZufall(seed)
    n = n_min + r.unter(n_max - n_min + 1)
    kanten = set()
    if zusammenhaengend:
        for j in range(1, n):
            kanten.add((r.unter(j), j))
    for _ in range(r.unter(2 * n) + 1):
        a, b = r.unter(n), r.unter(n)
        if a != b:
            kanten.add((min(a, b), max(a, b)))
    return N.aus_kanten("Zufallsnetz", n, sorted(kanten))


@pytest.fixture
def hand():
    return N.handnetz()


@pytest.fixture
def sammel():
    return N.halle_mit_sammelpunkt()
