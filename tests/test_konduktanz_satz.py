"""Der Zusatz beim Befund „deutlich größer“ sagt nur, was die Konduktanz zeigt: gegen networkx als zweiten Rechenweg, über Netze, Verfahren und Regeln. Dazu die
zwei Seiten des Satzes „Eine andere Menge kann nach der Konduktanz besser sein als die gepflanzte, sie kann aber auch schlechter sein“."""

import networkx as nx

import lsn_constants as C
import lsn_evaluation as E
import lsn_netze as N
import lsn_scenario as S
from lsn_verfahren import schnitt


def _nx(g):
    return nx.Graph([(u, v) for u in range(g.n) for v in g.nb[u] if u < v])


def _faelle():
    yield S.baue(C.NETZ_HALLEN, a=8, z=4)
    yield S.baue(C.NETZ_HALLEN, a=4, z=4, start_halle="ecke")
    yield S.baue(C.NETZ_GEMEIN, n=960, groesse=20, aussen=3, seed=C.DEFAULT_SEED)
    yield S.baue(C.NETZ_GEMEIN, n=960, groesse=60, aussen=1, seed=3)
    for start in range(6):
        yield S.baue(C.NETZ_HAND, start_platz=start)
        yield S.baue(C.NETZ_SAMMEL, start_platz=start)


def test_zusatz_stimmt_mit_networkx_ueber_netze_und_verfahren():
    gesehen = {"besser": 0, "schlechter": 0}
    for sz in _faelle():
        G = _nx(sz.g)
        gepflanzt = nx.conductance(G, sz.ziel)
        faelle = [("pagerank", (b, e)) for b in (0.006, 0.04, 0.25) for e in (3e-4, 1e-3, 0.05)]
        faelle += [("gierig-entdeckt", b) for b in (14, 100, 1500, 10000)] + [("bfs", b) for b in (14, 100, 1500, 10000)]
        for verfahren, par in faelle:
            for regel in ("min", "tal0.4"):
                s = schnitt(sz.g, sz.ziel, sz.start, verfahren, par, regel)
                art, text = E.verdikt_ergebnis(s, sz, "X")
                if "deutlich größer" not in text:
                    assert "Nach der Konduktanz" not in text and "nach der Konduktanz" not in text
                    continue
                gefunden = nx.conductance(G, set(s.menge))
                if "Auch nach der Konduktanz ist sie schlechter" in text:
                    assert gefunden > gepflanzt
                    gesehen["schlechter"] += 1
                elif "nicht schlechter als die gepflanzte" in text:
                    assert gefunden <= gepflanzt + 1e-9
                    gesehen["besser"] += 1
                else:
                    assert "auf vier Stellen gleich" in text and abs(gefunden - gepflanzt) < 1e-4
    assert gesehen["besser"] > 0 and gesehen["schlechter"] > 0, gesehen


def test_eine_andere_menge_kann_besser_oder_schlechter_sein():
    # besser: im Hallenverbund haben die größeren Blöcke die kleinere Konduktanz
    stufen = E.treppe(N.hallenverbund(8, 8), 8, 8)
    assert stufen[1]["konduktanz"] < stufen[0]["konduktanz"] and stufen[2]["konduktanz"] < stufen[0]["konduktanz"]
    # schlechter: Breitensuche auf kleinen Gruppen mit Außengrad 3 findet eine viel größere Menge mit größerer Konduktanz
    sz = S.baue(C.NETZ_GEMEIN, n=960, groesse=20, aussen=3, seed=C.DEFAULT_SEED)
    G = _nx(sz.g)
    faelle = [schnitt(sz.g, sz.ziel, sz.start, "bfs", b, "min") for b in C.BUDGET_STUFEN]
    assert any(len(s.menge) > 1.5 * len(sz.ziel) and nx.conductance(G, set(s.menge)) > nx.conductance(G, sz.ziel) for s in faelle)
