"""Die zwei wachsenden Gegner: gierige Erweiterung (drei Fassungen) und Breitensuche-Kugel. Ohne Streamlit.

**Gierige Erweiterung:** Immer wird der Randplatz mit dem größten Anteil seiner Verbindungen in die Menge aufgenommen, bis das Volumen (Summe der Grade) das Budget B
erreicht. Drei Fassungen unterscheiden sich nur in der Startmenge und der Regel bei Gleichstand:

* `gierig-entdeckt`: Start s; bei Gleichstand der zuerst entdeckte Kandidat;
* `gierig-nachbar`: Startmenge s samt allen Nachbarn, dann dieselbe Regel (**Nachbarschafts-Start**);
* `gierig-grad`: Start s; bei Gleichstand der kleinere Grad, dann die kleinere Nummer.

Die Konduktanz wird beim Wachsen mitgeführt, ein zweiter Durchgang entfällt: Kantenzugriffe sind nur der Aufbau.

**Breitensuche-Kugel:** Breitensuche ab s bis zum Volumenbudget; sortiert nach (Abstand, größter Anteil der Nachbarn auf der vorigen Schale, Nummer), dann Sweep.
Kantenzugriffe: Aufbau und Sweep."""

import heapq
from collections import deque

GIERIG = ("gierig-entdeckt", "gierig-nachbar", "gierig-grad")


def gierig(g, s: int, budget: int, art: str):
    """Gibt (Aufnahmereihenfolge, Volumen nach jedem Schritt)."""
    if art not in GIERIG:
        raise ValueError(f"unbekannte Fassung {art}")
    nb, d = g.nb, g.d
    drin, links, alter = set(), {}, {s: 0}
    reihe, vols = [], []
    vol = 0
    haufen = []
    nach_grad = art == "gierig-grad"

    def nimm(u):
        nonlocal vol
        drin.add(u)
        reihe.append(u)
        vol += d[u]
        vols.append(vol)
        for v in nb[u]:
            if v not in drin:
                c = links.get(v, 0) + 1
                links[v] = c
                a = alter.setdefault(v, len(alter))
                zweit = (d[v], v) if nach_grad else (a, 0)
                heapq.heappush(haufen, (-c / d[v],) + zweit + (c, v))

    nimm(s)
    if art == "gierig-nachbar":
        for v in nb[s]:
            if v not in drin:
                alter.setdefault(v, len(alter))
                nimm(v)
    while haufen and vol < budget:
        eintrag = heapq.heappop(haufen)
        c, u = eintrag[-2], eintrag[-1]
        if u in drin or c != links[u]:            # veralteter Eintrag
            continue
        nimm(u)
    return reihe, vols


def start_laenge(g, s: int, art: str) -> int:
    """Länge der Startmenge: 1, beim Nachbarschafts-Start s und alle Nachbarn."""
    return 1 + len(g.nb[s]) if art == "gierig-nachbar" else 1


def budget_laenge(vols: list, budget: int, mindestens: int) -> int:
    """Länge der Reihe, die ein Lauf mit diesem Budget gehabt hätte: bis das Volumen das Budget erreicht, mindestens die Startmenge."""
    k = next((i + 1 for i, v in enumerate(vols) if v >= budget), len(vols))
    return min(len(vols), max(k, mindestens))


def bfs_kugel(g, s: int, budget: int):
    """Gibt (sortierte Reihe, Volumen der Kugel)."""
    tiefe = {s: 0}
    schlange = deque((s,))
    reihe, vol = [], 0
    while schlange and vol < budget:
        u = schlange.popleft()
        reihe.append(u)
        vol += g.d[u]
        for v in g.nb[u]:
            if v not in tiefe:
                tiefe[v] = tiefe[u] + 1
                schlange.append(v)

    def schluessel(u):
        if g.d[u] == 0:
            return (tiefe[u], 0.0, u)
        davor = sum(1 for v in g.nb[u] if tiefe.get(v, 10 ** 9) < tiefe[u])
        return (tiefe[u], -davor / g.d[u], u)

    return sorted(reihe, key=schluessel), vol
