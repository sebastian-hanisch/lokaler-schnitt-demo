"""Netze als Nachbarlisten (einfach, ungerichtet, ungewichtet): Handnetze, Hallenverbund und Zufallsgemeinschaften, mit und ohne Sammelpunkte.

Ohne Streamlit. Die Handnetze folgen dem gemeinsamen Baustein `trz_netze.py` der Reihe „Irrfahrten auf Netzen“ (zwei Dreiecke mit einer Tür, gleiche Knotennummern);
die großen Netze brauchen nur Nachbarlisten und stehen deshalb hier in einer eigenen, schlanken Form.

* **Handnetz „zwei Hallen“:** Dreiecke {0, 1, 2} und {3, 4, 5}, eine Tür 2–3.
* **Halle mit Sammelpunkt:** das Handnetz und Platz 6 mit Verbindungen zu 0, 1, 3, 4, 5.
  Zielmenge ist in beiden Handnetzen das Dreieck, in dem der Start liegt; Platz 6 gehört zu keinem der beiden.
* **Hallenverbund z×z, Hallen a×a:** Gitter mit Vierernachbarschaft; benachbarte Hallen sind je durch eine Tür in der mittleren Zeile (nebeneinander) bzw. Spalte
  (übereinander) verbunden, Zeile bzw. Spalte a // 2. Zielmenge ist die mittlere Halle (Zeile z // 2, Spalte z // 2 im Verbund).
* **Zufallsgemeinschaften:** Gruppen gleicher Größe; innerhalb einer Gruppe jede Verbindung mit Wahrscheinlichkeit 8/(g−1) (im Mittel 8 Nachbarn in der Gruppe),
  dazu je Platz Poisson(Außengrad) Anschlüsse, die zufällig gepaart werden (Paare innerhalb einer Gruppe entfallen, Doppelte auch). Zielmenge ist die erste Gruppe,
  der Start ein zufälliger Platz dieser Gruppe in der größten Zusammenhangskomponente.
* **Mit Sammelpunkten:** Zufallsgemeinschaften mit Außengrad 1 und zusätzliche Plätze mit sehr vielen Verbindungen (nah: mit `innen` Verbindungen in die Zielgruppe)."""

from dataclasses import dataclass, field

import numpy as np
from scipy.sparse import csr_matrix
from scipy.sparse.csgraph import connected_components

from lsn_zufall import BlockZufall, poisson_schwellen, schwelle_aus_wahrscheinlichkeit

INNENGRAD = 8


@dataclass(eq=False)
class Graph:
    name: str
    nb: list                       # aufsteigend sortierte Nachbarlisten
    d: list = field(default=None)  # Grade
    vol: int = 0                   # Summe der Grade, 2m

    def __post_init__(self):
        if self.d is None:
            self.d = [len(x) for x in self.nb]
        self.vol = sum(self.d)

    @property
    def n(self) -> int:
        return len(self.nb)

    @property
    def m(self) -> int:
        return self.vol // 2


def aus_kanten(name: str, n: int, kanten) -> Graph:
    """Netz aus einer Kantenliste; Schleifen und Knoten außerhalb 0 … n−1 werden abgewiesen, Doppelkanten ebenso."""
    nb = [set() for _ in range(n)]
    for u, v in kanten:
        if u == v or not (0 <= u < n and 0 <= v < n):
            raise ValueError(f"ungültige Kante ({u}, {v}) bei {n} Knoten")
        if v in nb[u]:
            raise ValueError("doppelte Kante")
        nb[u].add(v)
        nb[v].add(u)
    return Graph(name, [sorted(x) for x in nb])


def kanten_von(g: Graph) -> list:
    return [(u, v) for u in range(g.n) for v in g.nb[u] if u < v]


# ----------------------------------------------------------------------------------------------------------------------------------
# Handnetze
# ----------------------------------------------------------------------------------------------------------------------------------

HAND_KANTEN = ((0, 1), (1, 2), (0, 2), (3, 4), (4, 5), (3, 5), (2, 3))
HAND_POS = ((0.0, 1.4), (0.0, 0.0), (1.2, 0.7), (2.8, 0.7), (4.0, 0.0), (4.0, 1.4))
SAMMEL_POS = HAND_POS + ((2.0, 2.4),)
ZIEL_HAND = frozenset({0, 1, 2})
HAND_HALLEN = (ZIEL_HAND, frozenset({3, 4, 5}))


def hand_halle(start: int) -> frozenset:
    """Zielmenge der Handnetze: die Halle (das Dreieck), in der der Start liegt. Der Sammelpunkt 6 gehört zu keiner Halle und ist kein zulässiger Start."""
    for halle in HAND_HALLEN:
        if start in halle:
            return halle
    raise ValueError(f"Platz {start} gehört zu keiner Halle")


def handnetz() -> Graph:
    return aus_kanten("Handnetz zwei Hallen", 6, HAND_KANTEN)


def halle_mit_sammelpunkt() -> Graph:
    return aus_kanten("Halle mit Sammelpunkt", 7, HAND_KANTEN + tuple((6, v) for v in (0, 1, 3, 4, 5)))


# ----------------------------------------------------------------------------------------------------------------------------------
# Hallenverbund
# ----------------------------------------------------------------------------------------------------------------------------------

def hallenknoten(z: int, a: int, hz: int, hs: int, zeile: int, spalte: int) -> int:
    return ((hz * z + hs) * a + zeile) * a + spalte


def hallenverbund(z: int, a: int) -> Graph:
    """z×z Hallen zu je a×a Plätzen."""
    if z < 1 or a < 2:
        raise ValueError("z ≥ 1 und a ≥ 2")
    nb = [[] for _ in range(z * z * a * a)]

    def kante(u, v):
        nb[u].append(v)
        nb[v].append(u)

    mitte = a // 2
    for hz in range(z):
        for hs in range(z):
            basis = (hz * z + hs) * a * a
            for r in range(a):
                for s in range(a):
                    u = basis + r * a + s
                    if s + 1 < a:
                        kante(u, u + 1)
                    if r + 1 < a:
                        kante(u, u + a)
            if hs + 1 < z:
                kante(hallenknoten(z, a, hz, hs, mitte, a - 1), hallenknoten(z, a, hz, hs + 1, mitte, 0))
            if hz + 1 < z:
                kante(hallenknoten(z, a, hz, hs, a - 1, mitte), hallenknoten(z, a, hz + 1, hs, 0, mitte))
    return Graph(f"Hallenverbund {z}×{z}, Hallen {a}×{a}", [sorted(x) for x in nb])


def halle_plaetze(z: int, a: int, hz: int, hs: int) -> range:
    basis = (hz * z + hs) * a * a
    return range(basis, basis + a * a)


def mittlere_halle(z: int, a: int) -> frozenset:
    return frozenset(halle_plaetze(z, a, z // 2, z // 2))


def block_plaetze(z: int, a: int, zeilen: int, spalten: int) -> frozenset:
    """Block aus `zeilen` × `spalten` Hallen, der die mittlere Halle als letzte Zeile bzw. Spalte enthält (innerer Block bei z ≥ 4)."""
    oben, links = z // 2 - zeilen + 1, z // 2 - spalten + 1
    s = set()
    for i in range(zeilen):
        for j in range(spalten):
            s.update(halle_plaetze(z, a, oben + i, links + j))
    return frozenset(s)


def hallen_koordinate(z: int, a: int, u: int):
    """(x, y) für die Karte: Hallen mit einer Gitterbreite Abstand."""
    h, rest = divmod(u, a * a)
    hz, hs = divmod(h, z)
    r, s = divmod(rest, a)
    return float(hs * (a + 1) + s), float(-(hz * (a + 1) + r))


def hallen_name(z: int, a: int, u: int) -> str:
    h, rest = divmod(u, a * a)
    hz, hs = divmod(h, z)
    r, s = divmod(rest, a)
    return f"Halle ({hz},{hs}), Platz ({r},{s})"


# ----------------------------------------------------------------------------------------------------------------------------------
# Zufallsgemeinschaften
# ----------------------------------------------------------------------------------------------------------------------------------

_TRIL = {}


def _paare(g: int):
    """Alle Paare (i, j) mit i > j innerhalb einer Gruppe, in fester Reihenfolge."""
    if g not in _TRIL:
        _TRIL[g] = np.tril_indices(g, -1)
    return _TRIL[g]


def _innenkanten(rng: BlockZufall, zahl: int, g: int) -> np.ndarray:
    i, j = _paare(g)
    p = min(1.0, INNENGRAD / (g - 1))
    schwelle = np.uint64(schwelle_aus_wahrscheinlichkeit(p))
    teile = []
    for b in range(zahl):
        wahl = np.flatnonzero(rng.u53(len(i)) < schwelle)
        teile.append(np.stack([b * g + j[wahl], b * g + i[wahl]], axis=1))
    return np.concatenate(teile) if teile else np.zeros((0, 2), dtype=np.int64)


def _aussenkanten(rng: BlockZufall, n: int, g: int, aussen: float) -> np.ndarray:
    anzahl = np.searchsorted(poisson_schwellen(aussen), rng.u53(n), side="right")
    stummel = rng.mischen(np.repeat(np.arange(n), anzahl))
    halb = len(stummel) // 2
    paare = stummel[: 2 * halb].reshape(halb, 2)
    paare = paare[paare[:, 0] // g != paare[:, 1] // g]
    lo, hi = paare.min(axis=1), paare.max(axis=1)
    schluessel = np.unique(lo.astype(np.int64) * n + hi)
    return np.stack([schluessel // n, schluessel % n], axis=1)


def graph_aus_feld(name: str, n: int, kanten: np.ndarray) -> Graph:
    """Netz aus einem Feld verschiedener Kanten (Form m×2)."""
    u = np.concatenate([kanten[:, 0], kanten[:, 1]])
    v = np.concatenate([kanten[:, 1], kanten[:, 0]])
    ordnung = np.lexsort((v, u))
    ziele = v[ordnung].tolist()
    grad = np.bincount(u, minlength=n)
    grenzen = np.concatenate([[0], np.cumsum(grad)]).tolist()
    return Graph(name, [ziele[grenzen[i]:grenzen[i + 1]] for i in range(n)], grad.tolist())


def groesste_komponente(g: Graph) -> np.ndarray:
    """Wahr für die Plätze der größten Zusammenhangskomponente (bei Gleichstand die mit der kleinsten Komponentennummer)."""
    zeilen = np.repeat(np.arange(g.n), g.d)
    spalten = np.fromiter((v for x in g.nb for v in x), dtype=np.int64, count=g.vol)
    A = csr_matrix((np.ones(len(zeilen)), (zeilen, spalten)), shape=(g.n, g.n))
    _, marke = connected_components(A, directed=False)
    return marke == np.argmax(np.bincount(marke))


def gemeinschaften(n: int, groesse: int, aussen: float, seed: int):
    """Gibt (Netz, Zielmenge = erste Gruppe, Start). n wird auf ein Vielfaches der Gruppengröße abgerundet."""
    if groesse < 2 or n // groesse < 2:
        raise ValueError("Gruppen mit mindestens 2 Plätzen und mindestens 2 Gruppen")
    zahl = n // groesse
    n = zahl * groesse
    rng = BlockZufall(seed)
    innen = _innenkanten(rng, zahl, groesse)
    aus = _aussenkanten(rng, n, groesse, aussen)
    g = graph_aus_feld(f"Zufallsgemeinschaften, {zahl} Gruppen zu {groesse}, Außengrad {aussen:g}", n, np.concatenate([innen, aus]))
    gross = groesste_komponente(g)
    kandidaten = [u for u in range(groesse) if gross[u]]
    if not kandidaten:
        raise ValueError("kein Platz der Zielgruppe in der größten Komponente")
    return g, frozenset(range(groesse)), kandidaten[rng.unter(len(kandidaten))]


def mit_sammelpunkten(n: int, groesse: int, seed: int, zahl: int, innen: int, verbindungen: int):
    """Zufallsgemeinschaften (Außengrad 1) und `zahl` Sammelpunkte. innen > 0: je `innen` Verbindungen in die Zielgruppe und `verbindungen` nach außen;
    innen = 0: `verbindungen` zu zufälligen Plätzen im ganzen Netz. Gibt (Netz, Zielmenge, Start, Sammelpunkte)."""
    g, ziel, s = gemeinschaften(n, groesse, 1.0, seed)
    n0 = g.n
    rng = BlockZufall(seed ^ 0x5A5A5A5A5A5A)           # eigene Folge, damit das Grundnetz dasselbe bleibt wie ohne Sammelpunkte
    nb = [list(x) for x in g.nb]
    sammel = []
    for _ in range(zahl):
        h = len(nb)
        if innen:
            ziele = rng.stichprobe(groesse, innen).tolist() + (groesse + rng.stichprobe(n0 - groesse, verbindungen)).tolist()
        else:
            ziele = rng.stichprobe(n0, verbindungen).tolist()
        nb.append(sorted(ziele))
        for v in ziele:
            nb[v].append(h)                              # h ist größer als alle bisherigen Nummern: die Liste bleibt sortiert
        sammel.append(h)
    name = f"{g.name}, {zahl} Sammelpunkte" if zahl else g.name
    return Graph(name, nb), ziel, s, frozenset(sammel)
