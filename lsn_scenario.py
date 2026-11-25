"""Aus den Einstellungen das Netz, die gepflanzte Zielmenge, den Startplatz und die Darstellung bauen. Ohne Streamlit."""

from dataclasses import dataclass

import lsn_constants as C
import lsn_netze as N
from lsn_zufall import BlockZufall


@dataclass(eq=False)
class Szenario:
    netz: str
    g: N.Graph
    ziel: frozenset
    start: int
    familie: str | None          # Abstimmfamilie ('a1', 'a3', 'hallen') oder None bei den Handnetzen
    sammel: frozenset = frozenset()
    z: int = 0                   # Hallenverbund
    a: int = 0

    def position(self, u: int):
        if self.netz == C.NETZ_HALLEN:
            return N.hallen_koordinate(self.z, self.a, u)
        if self.netz == C.NETZ_SAMMEL:
            return N.SAMMEL_POS[u]
        return N.HAND_POS[u]

    def platz_name(self, u: int) -> str:
        if self.netz == C.NETZ_HALLEN:
            return N.hallen_name(self.z, self.a, u)
        if u in self.sammel:
            return f"Sammelpunkt {u} ({self.g.d[u]} Verbindungen)"
        return f"Platz {u}"

    @property
    def hat_karte(self) -> bool:
        return self.netz in (C.NETZ_HAND, C.NETZ_SAMMEL, C.NETZ_HALLEN)


def hallen_startplatz(z: int, a: int, wahl: str, seed: int) -> int:
    """Startplatz in der mittleren Halle: Mitte, Ecke (0, 0), Platz an der linken Tür oder zufällig."""
    h = z // 2
    if wahl == "mitte":
        return N.hallenknoten(z, a, h, h, a // 2, a // 2)
    if wahl == "ecke":
        return N.hallenknoten(z, a, h, h, 0, 0)
    if wahl == "tuer":
        return N.hallenknoten(z, a, h, h, a // 2, 0)
    if wahl == "zufall":
        plaetze = sorted(N.mittlere_halle(z, a))
        return plaetze[BlockZufall(seed).unter(len(plaetze))]
    raise ValueError(f"unbekannte Startwahl {wahl}")


def plaetze_gewirkt(n: int, groesse: int) -> int:
    """Wirkende Netzgröße: mindestens zwei Gruppen (sonst gäbe es kein „außen“)."""
    return max(n, 2 * groesse)


def baue(netz: str, a: int = 8, z: int = 8, groesse: int = 60, aussen: int = 1, n: int = 16000, sammelart: str = "nah", start_platz: int = 0,
         start_halle: str = "mitte", seed: int = C.DEFAULT_SEED) -> Szenario:
    if netz == C.NETZ_HAND:
        return Szenario(netz, N.handnetz(), N.hand_halle(int(start_platz)), int(start_platz), None)
    if netz == C.NETZ_SAMMEL:
        return Szenario(netz, N.halle_mit_sammelpunkt(), N.hand_halle(int(start_platz)), int(start_platz), None, frozenset({6}))
    if netz == C.NETZ_HALLEN:
        return Szenario(netz, N.hallenverbund(z, a), N.mittlere_halle(z, a), hallen_startplatz(z, a, start_halle, seed), "hallen", z=z, a=a)
    if netz == C.NETZ_GEMEIN:
        g, ziel, s = N.gemeinschaften(plaetze_gewirkt(n, groesse), groesse, float(aussen), seed)
        return Szenario(netz, g, ziel, s, f"a{aussen}")
    if netz == C.NETZ_NADELN:
        anzahl, innen, weitere, _ = _sammel_parameter(sammelart)
        g, ziel, s, sammel = N.mit_sammelpunkten(n, 60, seed, anzahl, innen, weitere)
        return Szenario(netz, g, ziel, s, "a1", sammel)
    raise ValueError(f"unbekanntes Netz {netz}")


def _sammel_parameter(art: str):
    from lsn_messen import SAMMEL_ARTEN
    return SAMMEL_ARTEN[art]


def ausschnitt(sz: Szenario, hallen: int = 3):
    """Plätze, die auf der Karte gezeichnet werden: im Hallenverbund ein Block aus `hallen`×`hallen` Hallen um die mittlere Halle, sonst alle."""
    if sz.netz != C.NETZ_HALLEN:
        return list(range(sz.g.n))
    z, a = sz.z, sz.a
    mitte = z // 2
    erste = max(0, min(mitte - hallen // 2, z - hallen))
    reihen = range(erste, min(z, erste + hallen))
    return [u for hz in reihen for hs in reihen for u in N.halle_plaetze(z, a, hz, hs)]
