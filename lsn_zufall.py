"""SplitMix64 blockweise (numpy) und plattformfeste Hilfen für Netzerzeuger und Wärmeleitung.

`BlockZufall` ist aus `trefferzeit-demo/trz_irrfahrt_sim.py` übernommen und liefert exakt dieselbe Folge wie `lsn_rng.SplitMix64` (Test: `tests/test_zufall.py`):
der k-te Wert ist die Mischung von Zufalls-Seed + k·γ, also lassen sich ganze Blöcke auf einmal rechnen. Gezogen wird nur ganzzahlig; Vergleiche mit
Wahrscheinlichkeiten laufen über ganzzahlige Schwellen, die mit `decimal` gerechnet werden. So entstehen auf jeder Plattform dieselben Netze."""

import decimal

import numpy as np

GAMMA = np.uint64(0x9E3779B97F4A7C15)
_M1 = np.uint64(0xBF58476D1CE4E5B9)
_M2 = np.uint64(0x94D049BB133111EB)
MASK = (1 << 64) - 1
_BIT53 = 1 << 53
_CTX = decimal.Context(prec=45)


class BlockZufall:
    """SplitMix64 blockweise: `u64(m)` sind die nächsten m Werte der Folge."""

    def __init__(self, seed: int):
        self.seed = int(seed) & MASK
        self.gezogen = 0

    def u64(self, m: int) -> np.ndarray:
        nummer = np.arange(self.gezogen + 1, self.gezogen + m + 1, dtype=np.uint64)
        self.gezogen += m
        z = nummer * GAMMA + np.full(m, self.seed, dtype=np.uint64)      # uint64-Felder rechnen modulo 2^64
        z = (z ^ (z >> np.uint64(30))) * _M1
        z = (z ^ (z >> np.uint64(27))) * _M2
        return z ^ (z >> np.uint64(31))

    def u53(self, m: int) -> np.ndarray:
        """Die oberen 53 Bit als ganze Zahl in 0 … 2^53−1 (entspricht `random()` mal 2^53)."""
        return self.u64(m) >> np.uint64(11)

    def unter(self, n: int) -> int:
        """Eine ganze Zahl in 0 … n−1."""
        return int(self.u64(1)[0]) % n

    def stichprobe(self, n: int, k: int) -> np.ndarray:
        """k verschiedene Zahlen aus 0 … n−1: die Plätze der k kleinsten von n Zufallsschlüsseln, in Schlüsselreihenfolge."""
        return np.argsort(self.u64(n), kind="stable")[:k]

    def mischen(self, feld: np.ndarray) -> np.ndarray:
        """Zufällige Reihenfolge (Sortieren nach Zufallsschlüsseln)."""
        return feld[np.argsort(self.u64(len(feld)), kind="stable")]


def schwelle_aus_wahrscheinlichkeit(p: float) -> int:
    """Ganzzahlige Schwelle t mit P(u53 < t) = floor(p·2^53) / 2^53."""
    return int(decimal.Decimal(p) * _BIT53)


def exact_exp(x: float) -> float:
    """e^x, auf jeder Plattform bitgleich (mit `decimal` in 45 Stellen, dann einmal auf double gerundet)."""
    return float(_CTX.exp(decimal.Decimal(x)))


def poisson_schwellen(mittel: float, bis: int = 40) -> np.ndarray:
    """Schwellen der Verteilungsfunktion von Poisson(mittel) auf der Skala 0 … 2^53; die Zahl der Schwellen unter einem u53-Wert ist die Ziehung."""
    lam = decimal.Decimal(mittel)
    term = _CTX.exp(-lam)
    summe = term
    schwellen = []
    for k in range(bis):
        schwellen.append(int(_CTX.multiply(summe, decimal.Decimal(_BIT53))))
        term = _CTX.divide(_CTX.multiply(term, lam), decimal.Decimal(k + 1))
        summe = _CTX.add(summe, term)
    return np.array(schwellen, dtype=np.uint64)
