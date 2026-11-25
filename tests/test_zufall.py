"""Block-Zufall: dieselbe Folge wie die Klasse SplitMix64; ganzzahlige Schwellen und die exakte e-Funktion."""

import math
from fractions import Fraction

import numpy as np

from lsn_rng import SplitMix64
from lsn_zufall import BlockZufall, exact_exp, poisson_schwellen, schwelle_aus_wahrscheinlichkeit


def test_block_gleich_einzelfolge_auch_ueber_mehrere_bloecke():
    for seed in (0, 1, 2 ** 63 + 5, 8200012345):
        einzeln = SplitMix64(seed)
        block = BlockZufall(seed)
        werte = np.concatenate([block.u64(7), block.u64(1), block.u64(30)])
        assert werte.tolist() == [einzeln.next_u64() for _ in range(38)]


def test_u53_entspricht_random():
    einzeln, block = SplitMix64(5), BlockZufall(5)
    for x in block.u53(20).tolist():
        assert x / float(1 << 53) == einzeln.random()


def test_schwelle_ist_die_abgerundete_wahrscheinlichkeit():
    for p in (0.25, 8 / 59, 1.0, 0.1):
        t = schwelle_aus_wahrscheinlichkeit(p)
        assert Fraction(t, 1 << 53) <= Fraction(p) < Fraction(t + 1, 1 << 53)


def test_poisson_schwellen_gegen_die_summenformel():
    for lam in (1.0, 3.0):
        t = poisson_schwellen(lam).astype(float) / float(1 << 53)
        summe = 0.0
        for k in range(8):
            summe += math.exp(-lam) * lam ** k / math.factorial(k)
            assert abs(t[k] - summe) < 1e-12
        assert np.all(np.diff(t) >= 0) and t[-1] > 1 - 1e-12


def test_poisson_ziehung_trifft_mittel():
    z = np.searchsorted(poisson_schwellen(3.0), BlockZufall(3).u53(200000), side="right")
    assert abs(z.mean() - 3.0) < 0.02 and abs(z.var() - 3.0) < 0.05


def test_stichprobe_ohne_wiederholung_und_mischen():
    x = BlockZufall(4).stichprobe(100, 30)
    assert len(set(x.tolist())) == 30 and x.max() < 100
    m = BlockZufall(4).mischen(np.arange(50))
    assert sorted(m.tolist()) == list(range(50)) and m.tolist() != list(range(50))


def test_exact_exp():
    for x in (-80.0, -10.0, -0.25, 0.0, 2.5):
        assert abs(exact_exp(x) - math.exp(x)) <= 2 * math.ulp(math.exp(x))
