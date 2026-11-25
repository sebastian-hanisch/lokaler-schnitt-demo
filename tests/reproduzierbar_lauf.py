"""Hilfsskript zu test_reproduzierbar.py: baut je ein Netz je Art und gibt Prüfsummen und Schnitte aus."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import lsn_netze as N  # noqa: E402
from lsn_verfahren import laufe  # noqa: E402

KEYS = [("pagerank", (0.006, 3e-4), "min"), ("gierig-nachbar", 1000, "tal0.1"), ("waerme", (10, 3e-5), "tal0.1"), ("bfs", 600, "min")]

faelle = [N.gemeinschaften(1920, 60, 3.0, 42), N.mit_sammelpunkten(1920, 60, 43, 5, 12, 300)[:3],
          (N.hallenverbund(4, 6), N.mittlere_halle(4, 6), 500)]
for g, ziel, s in faelle:
    print(g.n, g.vol, s, sum((i + 1) * v for i, x in enumerate(g.nb) for v in x) % 1_000_000_007)
    for k, e in laufe(g, ziel, s, KEYS).items():
        print(k, repr(e.f1), e.zugriffe, e.groesse)
