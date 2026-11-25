"""Die Messreihen: Fälle mit festen Zufalls-Seeds, Raster, Auswahlregel und Zählungen. Ohne Streamlit.

`tools/vorrechnen.py` rechnet damit `daten/vorgerechnet.json`; die Tests rechnen einzelne Fälle derselben Definitionen nach.

**Abstimmung (nur für die Wahl der Einstellungen):** Zufallsgemeinschaften mit 16 000 Plätzen, Gruppengrößen 30 bis 480, je 8 Netze und Außengrad; Hallenverbund 6×6,
Hallenseiten 6, 8, 12, 16, je 16 Startplätze der mittleren Halle. **Test (eigene Zufalls-Seeds):** Gruppengrößen 20 bis 960, je 60 Netze und Außengrad (20 und 960 liegen
außerhalb der Abstimmung); Hallenverbund 8×8, Hallenseiten 6 bis 20, alle Startplätze der mittleren Halle. Um eine innere Halle sind beide Verbünde gleich aufgebaut: für
die abgestimmten Hallenseiten ist der Test keine unabhängige Prüfung.

**Auswahlregel:** je Verfahren und Sweep-Familie (`min` bzw. „erstes Tal“) das höchste mittlere F1 auf den Abstimm-Fällen (Zellen gleich gewichtet); unter allen
Einstellungen innerhalb 0,005 davon die mit den wenigsten Kantenzugriffen (Mittel der Zellen-Mediane). **Haupteinstellung** eines Verfahrens: die Sweep-Familie mit dem
höheren Abstimm-Wert."""

import lsn_netze as N
from lsn_verfahren import GIERIG, kennzahlen, median
from lsn_zufall import BlockZufall

GEWAEHLTE_TALSCHWELLEN = (0.02, 0.05, 0.1, 0.2, 0.4, 0.8, 1.6)
REGELN = ("min",) + tuple(f"tal{g:g}" for g in GEWAEHLTE_TALSCHWELLEN)
BUDGETS = (300, 450, 600, 1000, 1500, 2200, 3300, 5000, 6500, 10000, 14000, 20000, 28000)
BFS_BUDGETS = (300, 600, 1200, 2500, 5000, 10000, 20000, 40000)
BETAS = (0.00075, 0.0015, 0.003, 0.006, 0.015, 0.04)
EPSILON = (1e-3, 5e-4, 3e-4, 2e-4, 1e-4, 6e-5, 3e-5, 1.5e-5)
ZEITEN = (5, 10, 20, 40, 80)
DELTAS = (1e-3, 3e-4, 1e-4, 3e-5, 1e-5)
TOLERANZ_WAHL = 0.005

FAMILIEN = ("a1", "a3", "hallen")
FAMILIE_TEXT = {"a1": "Zufallsgemeinschaften, Außengrad 1", "a3": "Zufallsgemeinschaften, Außengrad 3", "hallen": "Hallenverbund"}
AUSSENGRAD = {"a1": 1.0, "a3": 3.0}
N_STANDARD = 16000
GROESSEN_TEST = (20, 30, 60, 120, 240, 480, 960)
GROESSEN_ABST = (30, 60, 120, 240, 480)
SEITEN_TEST = (6, 8, 10, 12, 16, 20)
SEITEN_ABST = (6, 8, 12, 16)
NETZE_ABST = 8
STARTS_ABST = 16
NETZE_TEST = 60
VERBUND_ABST = 6
VERBUND_TEST = 8
VERFAHREN_VERGLEICH = GIERIG + ("pagerank", "waerme", "bfs")
SWEEPS = ("min", "tal")

# Basis der Zufalls-Seeds je Messreihe (Seed = Basis·10^7 + Außengrad·10^6 + Größe·100 + Nummer); die Bereiche überschneiden sich nicht.
BASIS = {"abst": 81, "test": 82, "hallen_abst": 83, "n_reihe": 84, "sammel_nah": 85, "sammel_fern40": 86, "sammel_fern200": 87, "regel": 88, "verbund_reihe": 89,
         "fiedler": 90, "sammel_ohne": 91}


def seed_von(reihe: str, aussen: int = 0, groesse: int = 0, nummer: int = 0) -> int:
    return BASIS[reihe] * 10 ** 7 + aussen * 10 ** 6 + groesse * 100 + nummer


def zufallsauswahl(plaetze, zahl: int, seed: int) -> list:
    """`zahl` verschiedene Elemente aus der sortierten Liste, in gezogener Reihenfolge."""
    sortiert = sorted(plaetze)
    return [sortiert[i] for i in BlockZufall(seed).stichprobe(len(sortiert), zahl)]


# ----------------------------------------------------------------------------------------------------------------------------------
# Fälle
# ----------------------------------------------------------------------------------------------------------------------------------

def abstimm_faelle(familie: str):
    """(Zelle, Nummer, Bauvorschrift) in fester Reihenfolge; die Bauvorschrift gibt (Netz, Zielmenge, Start)."""
    if familie == "hallen":
        for a in SEITEN_ABST:
            netz = _verbund(VERBUND_ABST, a)
            ziel = N.mittlere_halle(VERBUND_ABST, a)
            for i, s in enumerate(zufallsauswahl(ziel, STARTS_ABST, seed_von("hallen_abst", 0, a))):
                yield a, i, (lambda netz=netz, ziel=ziel, s=s: (netz, ziel, s))
        return
    aussen = AUSSENGRAD[familie]
    for i in range(NETZE_ABST):
        for g in GROESSEN_ABST:
            seed = seed_von("abst", int(aussen), g, i)
            yield g, i, (lambda g=g, seed=seed: N.gemeinschaften(N_STANDARD, g, aussen, seed))


def test_fall(familie: str, zelle: int, nummer: int):
    if familie == "hallen":
        netz = _verbund(VERBUND_TEST, zelle)
        ziel = N.mittlere_halle(VERBUND_TEST, zelle)
        return netz, ziel, sorted(ziel)[nummer]
    aussen = AUSSENGRAD[familie]
    return N.gemeinschaften(N_STANDARD, zelle, aussen, seed_von("test", int(aussen), zelle, nummer))


def test_zellen(familie: str):
    return SEITEN_TEST if familie == "hallen" else GROESSEN_TEST


def innere_zellen(familie: str):
    return SEITEN_ABST if familie == "hallen" else GROESSEN_ABST


def test_nummern(familie: str, zelle: int):
    return range(zelle * zelle if familie == "hallen" else NETZE_TEST)


def test_faelle(familie: str):
    for zelle in test_zellen(familie):
        for i in test_nummern(familie, zelle):
            yield zelle, i, (lambda zelle=zelle, i=i: test_fall(familie, zelle, i))


_VERBUENDE = {}


def _verbund(z: int, a: int):
    if (z, a) not in _VERBUENDE:
        _VERBUENDE[(z, a)] = N.hallenverbund(z, a)
    return _VERBUENDE[(z, a)]


# ----------------------------------------------------------------------------------------------------------------------------------
# Raster und Auswahl
# ----------------------------------------------------------------------------------------------------------------------------------

def parameter(verfahren: str) -> tuple:
    if verfahren == "pagerank":
        return tuple((b, e) for b in BETAS for e in EPSILON)
    if verfahren == "waerme":
        return tuple((t, d) for t in ZEITEN for d in DELTAS)
    if verfahren == "bfs":
        return BFS_BUDGETS
    return BUDGETS


GRUPPEN = {"gierig": GIERIG + ("bfs",), "pagerank": ("pagerank",), "waerme": ("waerme",)}


def raster(gruppe: str) -> list:
    return [(v, p, r) for v in GRUPPEN[gruppe] for p in parameter(v) for r in REGELN]


def sweep_familie(regel: str) -> str:
    return "min" if regel == "min" else "tal"


def am_rand(verfahren: str, par) -> list:
    """Welche Parameter an einem Ende ihres Rasters liegen."""
    if verfahren == "pagerank":
        return [name for name, x, r in (("beta", par[0], BETAS), ("eps", par[1], EPSILON)) if x in (min(r), max(r))]
    if verfahren == "waerme":
        return [name for name, x, r in (("t", par[0], ZEITEN), ("delta", par[1], DELTAS)) if x in (min(r), max(r))]
    r = parameter(verfahren)
    return ["B"] if par in (min(r), max(r)) else []


def waehle_einstellungen(ergebnisse: dict, zellen) -> dict:
    """ergebnisse: {(Zelle, Nummer): {Schlüssel: Ergebnis}}. Gibt {Verfahren: {Sweep-Familie: Wahl}} nach der Auswahlregel."""
    je_zelle = {z: [w for (zz, _), w in sorted(ergebnisse.items()) if zz == z] for z in zellen}
    schluessel = list(next(iter(ergebnisse.values())))
    erg = {}
    for verfahren in VERFAHREN_VERGLEICH:
        for sweep in SWEEPS:
            kandidaten = []
            for k in schluessel:
                if k[0] != verfahren or sweep_familie(k[2]) != sweep:
                    continue
                mittel = sum(sum(w[k][0] for w in je_zelle[z]) / len(je_zelle[z]) for z in zellen) / len(zellen)
                zugriffe = sum(median([w[k][1] for w in je_zelle[z]]) for z in zellen) / len(zellen)
                kandidaten.append((mittel, zugriffe, repr(k), k))
            hoch = max(c[0] for c in kandidaten)
            mittel, zugriffe, _, k = min((c for c in kandidaten if c[0] >= hoch - TOLERANZ_WAHL), key=lambda c: (c[1], c[2]))
            erg.setdefault(verfahren, {})[sweep] = {
                "par": k[1], "regel": k[2], "abst_mittel": mittel, "abst_zugriffe": zugriffe, "abst_hoechstwert": hoch, "rand": am_rand(verfahren, k[1]),
            }
    return erg


def schluessel_aus_wahl(verfahren: str, wahl: dict) -> tuple:
    par = wahl["par"]
    return (verfahren, tuple(par) if isinstance(par, list) else par, wahl["regel"])


def haupt_sweep(wahl_familie: dict, verfahren: str) -> str:
    """Die auf den Abstimm-Fällen bessere Sweep-Familie (bei Gleichstand `min`)."""
    zeilen = wahl_familie[verfahren]
    return "tal" if zeilen["tal"]["abst_mittel"] > zeilen["min"]["abst_mittel"] else "min"


def beste_gierige(wahl_familie: dict) -> tuple:
    """(Fassung, Sweep-Familie) mit dem höchsten Abstimm-Wert unter den drei gierigen Fassungen."""
    kandidaten = [(wahl_familie[v][s]["abst_mittel"], v, s) for v in GIERIG for s in SWEEPS]
    _, v, s = max(kandidaten, key=lambda c: c[0])
    return v, s


def zaehlung(test: dict, wahl: dict, pagerank_sweep: str = "tal", gegner: str = "pagerank") -> dict:
    """Zählung über die Zellen innerhalb der Abstimmbereiche: je Familie die auf den Abstimm-Fällen beste gierige Einstellung gegen `gegner`.

    test: {Familie: {Zelle: {Verfahren: {Sweep: Kennzahlen}}}}. „Median mindestens so gut“ vergleicht auf zwei Stellen gerundet; „vorn“ bzw. „zurück“: Mittel um mehr
    als 0,02 höher bzw. niedriger. gegner='waerme' nimmt die Haupteinstellung der Wärmeleitung."""
    summe = {"zellen": 0, "median": 0, "treffer": 0, "vorn": 0, "zurueck": 0, "sparsamer": 0, "treffer_je_familie": {}, "gegner_treffer_vorn_je_familie": {}}
    faktoren = []
    for familie in FAMILIEN:
        gv, gs = beste_gierige(wahl[familie])
        sweep = pagerank_sweep if gegner == "pagerank" else haupt_sweep(wahl[familie], gegner)
        mindestens = strikt_gegner = 0
        for z in innere_zellen(familie):
            a = test[familie][z][gv][gs]
            b = test[familie][z][gegner][sweep]
            summe["zellen"] += 1
            summe["median"] += round(a["median"], 2) >= round(b["median"], 2)
            summe["treffer"] += a["treffer"] >= b["treffer"]
            mindestens += a["treffer"] >= b["treffer"]
            strikt_gegner += b["treffer"] > a["treffer"]
            summe["vorn"] += a["mittel"] > b["mittel"] + 0.02
            summe["zurueck"] += b["mittel"] > a["mittel"] + 0.02
            summe["sparsamer"] += a["zugriffe"] < b["zugriffe"]
            faktoren.append(b["zugriffe"] / a["zugriffe"])
        summe["treffer_je_familie"][familie] = (mindestens, len(innere_zellen(familie)))
        summe["gegner_treffer_vorn_je_familie"][familie] = (strikt_gegner, len(innere_zellen(familie)))
    summe["faktor_min"], summe["faktor_max"] = min(faktoren), max(faktoren)
    return summe


def zellen_kennzahlen(ergebnisse: dict, wahl_familie: dict, zellen) -> dict:
    """{Zelle: {Verfahren: {Sweep: Kennzahlen}}} aus den Testergebnissen."""
    erg = {}
    for z in zellen:
        netze = [w for (zz, _), w in sorted(ergebnisse.items()) if zz == z]
        erg[z] = {v: {s: kennzahlen([w[schluessel_aus_wahl(v, wahl_familie[v][s])] for w in netze]) for s in SWEEPS} for v in VERFAHREN_VERGLEICH}
    return erg


def test_schluessel(wahl_familie: dict) -> list:
    return sorted({schluessel_aus_wahl(v, wahl_familie[v][s]) for v in VERFAHREN_VERGLEICH for s in SWEEPS}, key=repr)


# ----------------------------------------------------------------------------------------------------------------------------------
# Zusatzmessungen: Gradfalle, Größe des Netzes, Sweep-Regel, Verbundgröße, Anteil in der Starthalle
# ----------------------------------------------------------------------------------------------------------------------------------

SAMMEL_ARTEN = {                       # Name: (Zahl, Verbindungen in die Zielgruppe, weitere Verbindungen, Messreihe)
    "ohne": (0, 0, 0, "sammel_ohne"),
    "nah": (5, 12, 300, "sammel_nah"),
    "fern40": (40, 0, 400, "sammel_fern40"),
    "fern200": (200, 0, 100, "sammel_fern200"),
}
SAMMEL_GRUPPE = 60
SAMMEL_NETZE = 96
SAMMEL_BETA = 0.006
SAMMEL_EPS = (1e-4, 3e-4, 1e-3)
SAMMEL_REGELN = ("min", "tal0.05", "tal0.2", "tal0.4")
ORDNUNGEN = ("p/Grad", "p")


def sammel_fall(art: str, nummer: int):
    zahl, innen, aussen, reihe = SAMMEL_ARTEN[art]
    return N.mit_sammelpunkten(N_STANDARD, SAMMEL_GRUPPE, seed_von(reihe, 0, 0, nummer), zahl, innen, aussen)


N_REIHE = (960, 4000, 16000, 64000)
N_REIHE_NETZE = 40
N_REIHE_GRUPPE = 60
PUSH_VORFUEHRUNG = (0.006, 3e-4)


def n_reihe_fall(n: int, nummer: int):
    return N.gemeinschaften(n, N_REIHE_GRUPPE, 1.0, seed_von("n_reihe", 0, 0, 0) + n * 100 + nummer)


def n_reihe_schluessel(wahl_a1: dict) -> dict:
    """Name → Schlüssel der Kurven in Experiment 3 (Außengrad 1)."""
    erg = {"push": ("pagerank", PUSH_VORFUEHRUNG, "min"), "push_traege": ("pagerank-traege", PUSH_VORFUEHRUNG, "min")}
    for v, name in (("pagerank", "abgestimmt"), ("waerme", "waerme")):
        erg[name] = schluessel_aus_wahl(v, wahl_a1[v][haupt_sweep(wahl_a1, v)])
    gv, gs = beste_gierige(wahl_a1)
    erg["gierig"] = schluessel_aus_wahl(gv, wahl_a1[gv][gs])
    return erg


VERBUND_REIHE_Z = (4, 8, 16, 32)
VERBUND_REIHE_A = 8
VERBUND_REIHE_STARTS = 20
VERBUND_REIHE_SCHLUESSEL = ("pagerank", (0.006, 1e-3), "min")


def verbund_reihe_faelle(z: int):
    netz = _verbund(z, VERBUND_REIHE_A)
    ziel = N.mittlere_halle(z, VERBUND_REIHE_A)
    for s in zufallsauswahl(ziel, VERBUND_REIHE_STARTS, seed_von("verbund_reihe", 0, z)):
        yield netz, ziel, s


REGEL_EPS = (1e-3, 3e-4, 1e-4)
REGEL_REGELN = ("min", "tal0.2", "tal0.4")
REGEL_BETA = 0.006
REGEL_FAELLE = {"hallen8": ("hallen", 8), "hallen16": ("hallen", 16), "a3_120": ("a3", 120), "a3_480": ("a3", 480)}
REGEL_NETZE = 60


def regel_faelle(name: str):
    art, wert = REGEL_FAELLE[name]
    if art == "hallen":
        netz = _verbund(VERBUND_TEST, wert)
        ziel = N.mittlere_halle(VERBUND_TEST, wert)
        for s in sorted(ziel):
            yield netz, ziel, s
        return
    for i in range(REGEL_NETZE):
        yield N.gemeinschaften(N_STANDARD, wert, 3.0, seed_von("regel", 3, wert, i))


def regel_schluessel() -> list:
    return [("pagerank", (REGEL_BETA, e), r) for e in REGEL_EPS for r in REGEL_REGELN]


FIEDLER_NETZE = 20          # Zufallsgemeinschaften für den Bezug „globaler Fiedler-Sweep“

ANTEIL_BETAS = (0.5, 0.25, 0.1, 0.04, 0.015, 0.006, 0.003, 0.0015, 0.00075)
ANTEIL_Z, ANTEIL_A = 8, 8
