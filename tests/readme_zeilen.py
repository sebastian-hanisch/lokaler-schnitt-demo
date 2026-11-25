"""Die Tabellenzeilen der README aus der Ergebnisdatei. `test_claims.py` verlangt jede dieser Zeilen wörtlich in der README; dieselben Daten rechnet es an
Stichproben aus dem Code nach."""

import lsn_evaluation as E
import lsn_messen as M

VERFAHREN_KURZ = {"gierig-entdeckt": "gierig „zuerst entdeckt“", "gierig-nachbar": "gierig Nachbarschafts-Start", "gierig-grad": "gierig „kleinerer Grad“",
                  "pagerank": "PageRank", "waerme": "Wärmeleitung", "bfs": "Breitensuche"}


def zelle(w: dict) -> str:
    return f"{E.de(w['median'], 2)} / {E.de(w['mittel'], 2)} / {w['treffer']}"


def kz(x: float) -> str:
    return E.ganz(x)


def zeile(*teile) -> str:
    return "| " + " | ".join(str(t) for t in teile) + " |"


def zeilen_wahl(d: dict) -> list:
    erg = []
    for fam in M.FAMILIEN:
        for v in M.VERFAHREN_VERGLEICH:
            for s in M.SWEEPS:
                w = d["wahl"][fam][v][s]
                stern = " ★" if M.haupt_sweep(d["wahl"][fam], v) == s else ""
                rand = ", ".join(w["rand"]) if w["rand"] else "–"
                erg.append(zeile(M.FAMILIE_TEXT[fam], VERFAHREN_KURZ[v] + stern, E.einstellung_text(M.schluessel_aus_wahl(v, w)), E.de(w["abst_mittel"], 3), rand))
    return erg


def zeilen_test(d: dict, fam: str, zeilen=None) -> list:
    """Haupteinstellungen und PageRank mit „min“."""
    erg = []
    paare = [(v, M.haupt_sweep(d["wahl"][fam], v)) for v in M.VERFAHREN_VERGLEICH]
    paare.insert(4, ("pagerank", "min"))
    for v, s in paare:
        name = VERFAHREN_KURZ[v] + (" („min“)" if v == "pagerank" and s == "min" else " ★" if M.haupt_sweep(d["wahl"][fam], v) == s else "")
        werte = [zelle(d["test"][fam][z][v][s]) for z in M.test_zellen(fam)]
        zugriffe = [d["test"][fam][z][v][s]["zugriffe"] for z in M.test_zellen(fam)]
        erg.append(zeile(name, *werte, f"{kz(min(zugriffe))} bis {kz(max(zugriffe))}"))
    return erg


def zeilen_n(d: dict) -> list:
    erg = []
    for name in ("push", "push_traege", "abgestimmt", "gierig", "waerme"):
        spalten = []
        for n in M.N_REIHE:
            e = d["n_reihe"][n]
            k = e["kurven"][name]
            spalten.append(f"{kz(k['zugriffe'])} ({E.de(k['zugriffe'] / e['vol'], 3)}) / {k['treffer']}")
        erg.append(zeile(E.N_REIHE_TEXT[name], *spalten))
    return erg


SAMMEL_ZEILEN = (("nah", 1e-4, "min"), ("nah", 1e-4, "tal0.2"), ("nah", 3e-4, "min"), ("nah", 3e-4, "tal0.2"), ("nah", 1e-3, "min"), ("nah", 1e-3, "tal0.2"),
                 ("fern40", 3e-4, "min"), ("fern40", 3e-4, "tal0.2"), ("fern200", 3e-4, "tal0.05"), ("fern200", 3e-4, "tal0.2"), ("fern200", 1e-3, "tal0.05"),
                 ("ohne", 3e-4, "min"), ("ohne", 3e-4, "tal0.05"))
SAMMEL_NAME = {"nah": "5 nahe", "fern40": "40 ferne (je 400)", "fern200": "200 ferne (je 100)", "ohne": "keine"}


def zeilen_sammel(d: dict) -> list:
    erg = []
    for art, eps, regel in SAMMEL_ZEILEN:
        a, b = E.sammel_zeile(d, art, eps, "p/Grad", regel), E.sammel_zeile(d, art, eps, "p", regel)
        erg.append(zeile(SAMMEL_NAME[art], E.zahl(eps), E.regel_anzeige(regel), f"{E.de(a['median'], 3)} / {E.de(a['mittel'], 3)} / {a['unter08']}",
                         f"{E.de(b['median'], 3)} / {E.de(b['mittel'], 3)} / {b['unter08']}"))
    return erg


def zeilen_regel(d: dict) -> list:
    erg = []
    for fall in M.REGEL_FAELLE:
        for eps in M.REGEL_EPS:
            r = {regel: d["regel"][fall][f"{eps:g}|{regel}"] for regel in M.REGEL_REGELN}
            erg.append(zeile(E.FALL_TEXT[fall], E.zahl(eps), *[f"{E.de(x['median'], 2)} / {x['treffer']} / {kz(x['groesse'])}" for x in r.values()],
                             kz(r["min"]["zugriffe"])))
    return erg


def zeilen_verbund(d: dict) -> list:
    return [zeile(f"{z}×{z}", kz(d["verbund_reihe"][z]["n"]), kz(d["verbund_reihe"][z]["zugriffe"]), f"{d['verbund_reihe'][z]['treffer']} von {d['verbund_reihe'][z]['zahl']}")
            for z in M.VERBUND_REIHE_Z]


def alle_zeilen(d: dict) -> list:
    erg = zeilen_wahl(d) + zeilen_n(d) + zeilen_sammel(d) + zeilen_regel(d) + zeilen_verbund(d)
    for fam in M.FAMILIEN:
        erg += zeilen_test(d, fam)
    return erg
