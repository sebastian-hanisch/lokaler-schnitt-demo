"""Alle Schnittverfahren hinter einer Schnittstelle: Schlüssel (Verfahren, Parameter, Sweep-Regel) → (F1, Kantenzugriffe, |S|, Menge). Ohne Streamlit.

Verfahren: `pagerank` (Parameter (β, ε), Push nicht träge), `pagerank-traege` (dasselbe in der trägen Fassung), `waerme` (Parameter (t, δ)),
`bfs` (Volumenbudget B), `gierig-entdeckt`, `gierig-nachbar`, `gierig-grad` (Volumenbudget B). Läufe mit gleichem Parameter und verschiedenen Sweep-Regeln
teilen sich die Rechnung. Kantenzugriffe: PageRank, Wärmeleitung und Breitensuche zählen Aufbau und Sweep, die gierige Erweiterung nur den Aufbau (sie führt die
Konduktanz beim Wachsen mit)."""

from typing import NamedTuple

import lsn_sweep as W
from lsn_diffusion import push, waerme
from lsn_wachsen import GIERIG, bfs_kugel, budget_laenge, gierig, start_laenge

ALLE = ("pagerank", "pagerank-traege", "waerme", "bfs") + GIERIG


class Ergebnis(NamedTuple):
    f1: float
    zugriffe: int
    groesse: int


class Schnitt(NamedTuple):
    ergebnis: Ergebnis
    menge: tuple          # gewählte Plätze in der Reihenfolge der Reihe
    reihe: tuple          # ganze Reihe, aus der gewählt wurde
    phis: tuple           # Konduktanz je Anfangsstück
    konduktanz: float
    werte: dict           # p bzw. h je Platz (leer bei gierig und Breitensuche)
    aufbau_zugriffe: int  # ohne Sweep


def reihe_und_zugriffe(g, s: int, verfahren: str, par):
    """(Reihe, Zugriffe des Aufbaus, Werte). Für die gierige Erweiterung steht hier die Volumenliste statt der Zugriffe."""
    if verfahren in ("pagerank", "pagerank-traege"):
        p, _, z, _ = push(g, s, par[0], par[1], traege=verfahren.endswith("traege"))
        return (W.reihe_nach(g, p) or [s]), z, p
    if verfahren == "waerme":
        h, z = waerme(g, s, par[0], par[1])
        return (W.reihe_nach(g, h) or [s]), z, h
    if verfahren == "bfs":
        reihe, z = bfs_kugel(g, s, par)
        return reihe, z, {}
    raise ValueError(f"unbekanntes Verfahren {verfahren}")


def schnitt(g, ziel, s: int, verfahren: str, par, regel: str, normiert: bool = True) -> Schnitt:
    """Ein Verfahren vollständig, mit Menge und Konduktanzkurve (für die Anzeige)."""
    if verfahren in GIERIG:
        reihe, vols = gierig(g, s, par, verfahren)
        phis, _ = W.kurve(g, reihe)
        k = W.waehle(phis, regel, budget_laenge(vols, par, start_laenge(g, s, verfahren)))
        menge = tuple(reihe[:k])
        erg = Ergebnis(W.f1(len(set(menge) & ziel), k, len(ziel)), vols[-1], k)
        return Schnitt(erg, menge, tuple(reihe), tuple(phis), phis[k - 1], {}, vols[-1])
    return schnitt_aus(g, ziel, s, reihe_und_zugriffe(g, s, verfahren, par), regel, normiert)


def schnitt_aus(g, ziel, s: int, ausbreitung, regel: str, normiert: bool = True) -> Schnitt:
    """Sweep über eine schon gerechnete Ausbreitung (Ergebnis von `reihe_und_zugriffe`); so teilen sich mehrere Regeln eine Rechnung."""
    reihe, z, werte = ausbreitung
    if not normiert and werte:
        reihe = W.reihe_nach(g, werte, normiert=False) or [s]
    phis, vols = W.kurve(g, reihe)
    k = W.waehle(phis, regel)
    menge = tuple(reihe[:k])
    erg = Ergebnis(W.f1(len(set(menge) & ziel), k, len(ziel)), z + vols[-1], k)
    return Schnitt(erg, menge, tuple(reihe), tuple(phis), phis[k - 1], werte, z)


def laufe(g, ziel, s: int, schluessel) -> dict:
    """Viele Einstellungen auf einem Netz: {Schlüssel: Ergebnis}. Gleiche Rechnungen werden nur einmal gemacht."""
    gruppen = {}
    for k in schluessel:
        verfahren, par, _ = k
        gruppen.setdefault((verfahren, None if verfahren in GIERIG else par), []).append(k)
    erg = {}
    for (verfahren, par), ks in gruppen.items():
        if verfahren in GIERIG:
            reihe, vols = gierig(g, s, max(k[1] for k in ks), verfahren)
            phis, _ = W.kurve(g, reihe)
            treffer = W.kumulierte_treffer(reihe, ziel)
            start = start_laenge(g, s, verfahren)
            for k in ks:
                laenge = budget_laenge(vols, k[1], start)
                wahl = W.waehle(phis, k[2], laenge)
                erg[k] = Ergebnis(W.f1(treffer[wahl], wahl, len(ziel)), vols[laenge - 1], wahl)
            continue
        reihe, z, _ = reihe_und_zugriffe(g, s, verfahren, par)
        phis, vols = W.kurve(g, reihe)
        treffer = W.kumulierte_treffer(reihe, ziel)
        for k in ks:
            wahl = W.waehle(phis, k[2])
            erg[k] = Ergebnis(W.f1(treffer[wahl], wahl, len(ziel)), z + vols[-1], wahl)
    return erg


def median(x) -> float:
    y = sorted(x)
    n = len(y)
    return (y[(n - 1) // 2] + y[n // 2]) / 2


def kennzahlen(ergebnisse) -> dict:
    """Median, Mittel, Treffer (F1 ≥ 0,9), Zahl, Median der Kantenzugriffe und der Mengengröße über eine Liste von Ergebnissen."""
    return {
        "median": median([e[0] for e in ergebnisse]),
        "mittel": sum(e[0] for e in ergebnisse) / len(ergebnisse),
        "treffer": sum(e[0] >= W.TREFFER_AB - 1e-12 for e in ergebnisse),
        "zahl": len(ergebnisse),
        "zugriffe": median([e[1] for e in ergebnisse]),
        "groesse": median([e[2] for e in ergebnisse]),
    }
