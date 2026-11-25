"""Kennzahlen für die App und die Verdikte als reine Funktionen (ohne Streamlit). Jedes Verdikt gibt (Art, Text) mit Art in success, info, warning."""

import math
from dataclasses import dataclass
from itertools import combinations

import lsn_constants as C
import lsn_messen as M
import lsn_netze as N
import lsn_scenario as S
import lsn_sweep as W
from lsn_diffusion import ppr_exakt, push
from lsn_verfahren import Schnitt, laufe, schnitt


@dataclass(frozen=True)
class Settings:
    netz: str
    a: int
    z: int
    groesse: int
    aussen: int
    n: int
    sammelart: str
    start_platz: int
    start_halle: str
    verfahren: str
    beta: float
    eps: float
    regel: str
    gamma: float
    gierig_art: str
    budget: int
    seed: int


def szenario(s: Settings) -> S.Szenario:
    return S.baue(s.netz, s.a, s.z, s.groesse, s.aussen, s.n, s.sammelart, s.start_platz, s.start_halle, s.seed)


def regel_text(regel: str, gamma: float) -> str:
    return "min" if regel == "min" else f"tal{gamma:g}"


def regel_anzeige(regel: str) -> str:
    g = W.regel_gamma(regel)
    return "„min“" if g is None else f"„erstes Tal“ mit Schwelle {de(g, 2, kurz=True)}"


def de(x: float, stellen: int = 2, kurz: bool = False) -> str:
    """Zahl mit Dezimalkomma und Tausenderpunkt-frei (schmales Leerzeichen als Tausendertrenner)."""
    if kurz:
        t = f"{x:.{stellen}f}".rstrip("0").rstrip(".")
    else:
        t = f"{x:.{stellen}f}"
    return t.replace(".", ",")


def ganz(x: float) -> str:
    return f"{int(round(x)):,}".replace(",", " ")


def anzahl(n: float, einzahl: str, mehrzahl: str) -> str:
    """Zahl mit Wort, bei genau 1 in der Einzahl."""
    return f"{ganz(n)} {einzahl if int(round(n)) == 1 else mehrzahl}"


def zahl(x: float) -> str:
    """Kleine Parameter (β, ε) ohne wissenschaftliche Schreibweise."""
    t = f"{x:.7f}".rstrip("0").rstrip(".")
    return t.replace(".", ",")


def feste_einstellung(wahl: dict, familie: str, verfahren: str) -> tuple:
    """Die auf den Abstimm-Fällen gewählte Haupteinstellung eines Verfahrens als Schlüssel (Verfahren, Parameter, Sweep-Regel)."""
    sweep = M.haupt_sweep(wahl[familie], verfahren)
    return M.schluessel_aus_wahl(verfahren, wahl[familie][verfahren][sweep])


def einstellung(s: Settings, sz: S.Szenario, wahl: dict, verfahren: str = None) -> tuple:
    """Schlüssel des gewählten Verfahrens: PageRank und gierig nach den Reglern, Wärmeleitung und Breitensuche mit der für die Netzfamilie abgestimmten
    Einstellung (auf den Handnetzen eine feste Vorgabe)."""
    verfahren = verfahren or s.verfahren
    if verfahren == "pagerank":
        return ("pagerank", (s.beta, s.eps), regel_text(s.regel, s.gamma))
    if verfahren == "gierig":
        return (s.gierig_art, s.budget, regel_text(s.regel, s.gamma))
    if sz.familie is None:
        return ("waerme", (3, 0.0), "min") if verfahren == "waerme" else ("bfs", sz.g.vol, "min")
    return feste_einstellung(wahl, sz.familie, verfahren)


def einstellung_text(schluessel: tuple) -> str:
    verfahren, par, regel = schluessel
    if verfahren.startswith("pagerank"):
        t = f"β = {zahl(par[0])}, ε = {zahl(par[1])}"
    elif verfahren == "waerme":
        t = f"t = {de(par[0], 0)}, δ = {zahl(par[1])}"
    else:
        t = f"B = {ganz(par)}"
    return f"{t}, {regel_anzeige(regel)}"


def konduktanz_vergleich(gefunden: float, sz: S.Szenario) -> str:
    """Satz, ob die gefundene Menge nach der Konduktanz schlechter (größerer Wert) ist als die gepflanzte; leer, wenn diese keine Konduktanz hat."""
    rand, vol = W.rand_und_volumen(sz.g, sz.ziel)
    nenner = min(vol, sz.g.vol - vol)
    if nenner <= 0:
        return ""
    gepflanzt = rand / nenner
    if gefunden <= gepflanzt + 1e-12:
        return (f" Nach der Konduktanz ist sie nicht schlechter als die gepflanzte (diese hat {de(gepflanzt, 4)}, kleiner ist besser); "
                "F1 zählt nur die Übereinstimmung mit der gepflanzten Menge.")
    if de(gefunden, 4) == de(gepflanzt, 4):
        return " Die Konduktanz beider Mengen ist auf vier Stellen gleich."
    return f" Auch nach der Konduktanz ist sie schlechter als die gepflanzte (diese hat {de(gepflanzt, 4)}, kleiner ist besser)."


def verdikt_ergebnis(s: Schnitt, sz: S.Szenario, name: str):
    e = s.ergebnis
    ziel = len(sz.ziel)
    text = f"{name} findet {anzahl(e.groesse, 'Platz', 'Plätze')} (gepflanzt: {ganz(ziel)}), F1 = {de(e.f1, 2)}, Konduktanz {de(s.konduktanz, 4)}."
    if e.f1 >= W.TREFFER_AB - 1e-12:
        return "success", text + " Treffer (F1 ≥ 0,9)."
    if e.groesse > 1.5 * ziel:
        return "warning", text + " Kein Treffer: die gefundene Menge ist deutlich größer als die gepflanzte." + konduktanz_vergleich(s.konduktanz, sz)
    if e.groesse < ziel / 1.5:
        return "warning", text + " Kein Treffer: die gefundene Menge ist deutlich kleiner als die gepflanzte."
    return "warning", text + " Kein Treffer: Größe ähnlich, aber andere Plätze."


def verdikt_aufwand(s: Schnitt, sz: S.Szenario, name: str):
    anteil = s.ergebnis.zugriffe / sz.g.vol
    text = f"{name} liest {ganz(s.ergebnis.zugriffe)} Kantenzugriffe, das ist {de(anteil, 2)}-mal die Summe aller Grade ({ganz(sz.g.vol)})."
    if anteil < 0.5:
        return "success", text + " Auf diesem Netz bleibt das Verfahren lokal."
    return "warning", text + " Auf diesem Netz ist das nicht lokal: Gelesen wird so viel wie ein großer Teil des ganzen Netzes oder mehr."


ANNAHMEN_MARKDOWN = """**Annahmen.**
- Einfaches, ungerichtetes, ungewichtetes Netz. Die Irrfahrt springt in jedem Schritt mit Wahrscheinlichkeit β zum Start zurück, sonst geht sie zu einem gleich wahrscheinlich gewählten Nachbarn (nicht träge).
- Der Push arbeitet eine Warteschlange ab (Anfang: Start). Die Reihenfolge gehört zur Definition; deshalb hängen die Push-Werte an der Nummerierung der Plätze.
- Sweep-Ordnung nach Wert geteilt durch Grad, bei Gleichstand nach Nummer. Treffer heißt F1 ≥ 0,9 gegen die gepflanzte Menge.
- Kantenzugriffe: Summe der Grade aller bearbeiteten Plätze. PageRank, Wärmeleitung und Breitensuche zählen Aufbau und Sweep, die gierige Erweiterung nur den Aufbau (sie führt die Konduktanz mit). Auch doppelt gezählt läge sie in den 14 Zellen unter dem PageRank-Schnitt. Warteschlangen- und Heap-Arbeit zählt nicht.

**Grenzen.**
- Alle Zahlen gelten für die synthetischen Netze der Demo (Gitterhallen und Zufallsgemeinschaften) und die genannten Einstellungen. Netze mit Ortsbezug, echte, gewichtete oder gerichtete Netze sind nicht gemessen.
- F1 misst nur gegen die gepflanzte Menge. Eine andere Menge kann nach der Konduktanz besser sein als die gepflanzte (im Hallenverbund mit a = 8 ist die Konduktanz zweier Nachbarhallen und eines Blocks 2×2 kleiner als die einer Halle), sie kann aber auch schlechter sein; beim Schnitt oben stehen deshalb auch Größe und Konduktanz.
- Die gierigen Regeln, der Nachbarschafts-Start und das „erste Tal“ entstanden nach Blick auf Ergebnisse; hier sind sie auf neuen Zufalls-Seeds gemessen, aber nicht auf neuen Netzarten.
- Für die abgestimmten Hallenseiten ist der Test auf den Hallen keine unabhängige Prüfung (um eine innere Halle sind Abstimm- und Testverbund gleich aufgebaut).
- Einige gewählte Einstellungen liegen am Rand ihres Rasters (Wärmeleitung bei Außengrad 3: kleinstes δ; auf den Hallen mit „erstem Tal“: größtes t; PageRank mit „min“ auf den Hallen: größtes ε; gierig „kleinerer Grad“ mit „min“ auf den Hallen: kleinstes B). Andere Rasterwerte könnten das Bild verschieben, vor allem die Zugriffe.
- Nicht gemessen: gierige Erweiterung mit Entfernen von Plätzen, Fluss-Verfahren, Nibble, Louvain oder Leiden von einem Start, hk-relax.

**Bekannte Probleme und Unsicherheiten.**
- Der Erfolg ist je Netz oft zweigipflig (fast ganz richtig oder weit daneben): Ein einzelnes Netz sagt wenig über ein Verfahren.
- Die Wärmeleitung ist eine eigene abgeschnittene Fassung, nicht das Verfahren von Kloster und Gleich.
- Bei sehr kleinem β und ε liest der Push auf den großen Hallennetzen mehrere Millionen Kantenzugriffe; dann dauert ein Lauf einige Sekunden.
- Nicht alle Quellen sind im Original gelesen (siehe „Mathematische Formulierung“)."""


# ----------------------------------------------------------------------------------------------------------------------------------
# Experiment 1: der Neustart
# ----------------------------------------------------------------------------------------------------------------------------------

@dataclass(eq=False)
class Neustart:
    p: object                  # exaktes personalisiertes PageRank (numpy)
    anteil_ziel: float
    betas: tuple
    anteile: tuple             # Anteil in der Zielmenge je β


def neustart(sz: S.Szenario, beta: float, betas=M.ANTEIL_BETAS) -> Neustart:
    p = ppr_exakt(sz.g, sz.start, beta)
    ziel = sorted(sz.ziel)
    anteile = tuple(float(ppr_exakt(sz.g, sz.start, b)[ziel].sum()) for b in betas)
    return Neustart(p, float(p[ziel].sum()), tuple(betas), anteile)


def push_protokoll(sz: S.Szenario, beta: float, eps: float, grenze: int = 200):
    """Schritte des Push auf kleinen Netzen (höchstens `grenze` Pushes werden mitgeschrieben)."""
    protokoll = []
    p, r, z, pushes = push(sz.g, sz.start, beta, eps, protokoll=protokoll, protokoll_grenze=grenze)
    return protokoll, p, r, z, pushes


def push_zaehlung(sz: S.Szenario, beta: float, eps: float):
    """(Pushes, Kantenzugriffe, berührte Plätze)."""
    p, r, z, pushes = push(sz.g, sz.start, beta, eps)
    return pushes, z, len(p.keys() | r.keys())


def invariante_abweichung(sz: S.Szenario, beta: float, p: dict, r: dict) -> float:
    """Größte Abweichung in p + ppr(r) = ppr(Start); ppr(r) ist die Summe r(v)·ppr(ab v). Für kleine Netze."""
    voll = ppr_exakt(sz.g, sz.start, beta)
    summe = [p.get(u, 0.0) for u in range(sz.g.n)]
    for v, rv in r.items():
        teil = ppr_exakt(sz.g, v, beta)
        summe = [x + rv * float(teil[u]) for u, x in enumerate(summe)]
    return max(abs(summe[u] - float(voll[u])) for u in range(sz.g.n))


def verdikt_neustart(sz: S.Szenario, beta: float, n: Neustart):
    ziel = "der Starthalle" if sz.netz != C.NETZ_GEMEIN and sz.netz != C.NETZ_NADELN else "der Zielgruppe"
    text = f"Mit β = {zahl(beta)} liegen auf diesem Netz ab diesem Start **{de(100 * n.anteil_ziel, 1)} %** des PageRank in {ziel}."
    if sz.netz == C.NETZ_HAND and abs(beta - 0.25) < 1e-12 and sz.start == 0:
        text += " Das sind genau 16/19."
    return "info", text


def verdikt_ordnung_und_regel(zeilen, ziel_groesse: int):
    """Kernfrage 3: dieselbe Gewichtung, drei Schnitte. zeilen: [(Beschriftung, Ergebnis)]."""
    teile = "; ".join(f"{name}: {anzahl(e.groesse, 'Platz', 'Plätze')} (F1 {de(e.f1, 2)})" for name, e in zeilen)
    groessen = [e.groesse for _, e in zeilen]
    f1s = [e.f1 for _, e in zeilen]
    text = f"Dasselbe PageRank, gepflanzt sind {ganz(ziel_groesse)} Plätze. {teile}."
    if max(f1s) - min(f1s) > 0.1 or max(groessen) > 1.5 * max(min(groessen), 1):
        return "warning", text + " Ordnung und Regel entscheiden hier, welche Menge herauskommt."
    return "info", (text + " Auf diesem Netz sind die drei Schnitte in Größe und F1 ähnlich (F1 höchstens 0,1 auseinander, die größte Menge höchstens das "
                    "1,5-Fache der kleinsten); das ist nicht auf jedem Netz so.")


def verdikt_anteil_gemessen(anteil: dict):
    """Verdikt zum gemessenen Satz „mit kleinerem β sinkt der Anteil in der Starthalle“ (Hallenverbund 8×8, a = 8, alle Startplätze der mittleren Halle)."""
    betas, med = anteil["betas"], anteil["median"]
    k, n = anteil["monoton"], anteil["starts"]
    text = (f"Gemessen im Hallenverbund 8×8 (a = 8), alle {n} Startplätze der mittleren Halle: Der Anteil in der Starthalle fiel mit jedem kleineren β der Reihe "
            f"{zahl(betas[0])} bis {zahl(betas[-1])} bei {k} von {n} Startplätzen; im Median von {de(100 * med[0], 1)} % auf {de(100 * med[-1], 1)} %.")
    return ("success" if k == n else "info"), text


# ----------------------------------------------------------------------------------------------------------------------------------
# Experiment 2: durch den Grad teilen
# ----------------------------------------------------------------------------------------------------------------------------------

def sammel_zeile(daten: dict, art: str, eps: float, ordnung: str, regel: str) -> dict:
    return daten["sammel"][art][f"{eps:g}|{ordnung}|{regel}"]


def verdikt_gradfalle(mit: dict, ohne: dict, art: str, eps: float, regel: str):
    kopf = f"{C.SAMMEL_TEXT[art][0].upper() + C.SAMMEL_TEXT[art][1:]}, ε = {zahl(eps)}, {regel_anzeige(regel)}, {len(mit['f1'])} Netze mit 16 000 Plätzen: "
    zahlen = f"F1-Median nach p/Grad {de(mit['median'], 3)}, nach p allein {de(ohne['median'], 3)} (Mittel {de(mit['mittel'], 3)} gegen {de(ohne['mittel'], 3)})."
    diff = mit["median"] - ohne["median"]
    if diff > 0.05:
        return "warning", kopf + zahlen + f" Ohne Division kommen im Mittel {de(ohne['sammel_mittel'], 2)} Sammelpunkte in den Schnitt, mit Division {de(mit['sammel_mittel'], 2)}."
    if mit["mittel"] - ohne["mittel"] > 0.05:
        return "warning", kopf + zahlen + " Im Median ist der Unterschied klein, im Mittel nicht: auf einem Teil der Netze schadet die Ordnung ohne Division deutlich."
    if ohne["mittel"] - mit["mittel"] > 0.05 or diff < -0.05:
        return "info", kopf + zahlen + " Hier schadet die Ordnung ohne Division nicht."
    return "info", kopf + zahlen + " In dieser Einstellung macht die Division im Median und im Mittel höchstens 0,05 Unterschied."


def zaehle_gradfalle(daten: dict, grenze: float = 0.05):
    """(Zellen, davon p/Grad im Median um mehr als `grenze` besser, davon p um mehr als `grenze` besser) über alle Bauarten mit Sammelpunkten, ε und Regeln."""
    zellen = besser = schlechter = 0
    for art in ("nah", "fern40", "fern200"):
        for eps in M.SAMMEL_EPS:
            for regel in M.SAMMEL_REGELN:
                a = sammel_zeile(daten, art, eps, "p/Grad", regel)["median"]
                b = sammel_zeile(daten, art, eps, "p", regel)["median"]
                zellen += 1
                besser += a - b > grenze + 1e-12
                schlechter += b - a > grenze + 1e-12
    return zellen, besser, schlechter


# ----------------------------------------------------------------------------------------------------------------------------------
# Experiment 3: gleich viel gelesen
# ----------------------------------------------------------------------------------------------------------------------------------

def gleich_viel(n_reihe: dict, name: str, ab: int = 4000):
    """(kleinster, größter) Median der Kantenzugriffe über die Netzgrößen ab `ab`."""
    werte = [n_reihe[n]["kurven"][name]["zugriffe"] for n in sorted(n_reihe) if n >= ab]
    return min(werte), max(werte)


def verdikt_gleich_viel(n_reihe: dict, beta: float, eps: float):
    groessen = sorted(n_reihe)
    klein, gross = gleich_viel(n_reihe, "push", groessen[1])
    am_anfang = n_reihe[groessen[0]]["kurven"]["push"]["zugriffe"] / n_reihe[groessen[0]]["vol"]
    text = (f"Auf wachsenden Zufallsgemeinschaften (Gruppen zu 60, Außengrad 1) liest der Push (β = {zahl(beta)}, ε = {zahl(eps)}, „min“) von "
            f"{ganz(groessen[1])} bis {ganz(groessen[-1])} Plätzen im Median {ganz(klein)} bis {ganz(gross)} Kantenzugriffe. Bei {ganz(groessen[0])} Plätzen ist das "
            f"{de(am_anfang, 2)}-mal die Summe aller Grade. Die Obergrenze 1/(β·ε) = {ganz(1 / (beta * eps))} hängt nicht von der Netzgröße ab (Satz).")
    art = "success" if gross <= 1.15 * klein else "warning"
    gegner = []
    for name, titel in (("gierig", "die gierige Erweiterung (durch ihr Budget)"), ("waerme", "die Wärmeleitung")):
        k, g = gleich_viel(n_reihe, name, groessen[1])
        if g <= 1.15 * k:
            gegner.append(titel)
    if gegner:
        text += " Auch " + " und ".join(gegner) + " lesen hier ab 4 000 Plätzen fast gleich viel; das unterscheidet den PageRank nicht."
    return art, text


def verdikt_gleich_viel_kurz(n_reihe: dict):
    """Kernfrage 2."""
    groessen = sorted(n_reihe)
    klein, gross = gleich_viel(n_reihe, "push", groessen[1])
    anteil_klein = n_reihe[groessen[1]]["kurven"]["push"]["zugriffe"] / n_reihe[groessen[1]]["vol"]
    anteil_gross = n_reihe[groessen[-1]]["kurven"]["push"]["zugriffe"] / n_reihe[groessen[-1]]["vol"]
    text = (f"Auf Zufallsgemeinschaften (Gruppen zu 60, Außengrad 1) liest der Push mit β = 0,006, ε = 0,0003 von {ganz(groessen[1])} bis {ganz(groessen[-1])} Plätzen "
            f"im Median {ganz(klein)} bis {ganz(gross)} Kantenzugriffe: bei {ganz(groessen[1])} Plätzen das {de(anteil_klein, 2)}-Fache der Summe aller Grade, bei "
            f"{ganz(groessen[-1])} das {de(anteil_gross, 3)}-Fache.")
    anfang = n_reihe[groessen[0]]["kurven"]["push"]["zugriffe"] / n_reihe[groessen[0]]["vol"]
    if anfang > 1:
        text += f" Bei {ganz(groessen[0])} Plätzen sind es {de(anfang, 2)}-mal so viele wie das ganze Netz."
    return "info", text


def tabelle_n(daten: dict, namen) -> list:
    """Zeilen je Netzgröße und Kurve für Experiment 3."""
    wahl = daten["wahl"]["a1"]
    schluessel = M.n_reihe_schluessel(wahl)
    zeilen = []
    for name in namen:
        for n in sorted(daten["n_reihe"]):
            eintrag = daten["n_reihe"][n]
            k = eintrag["kurven"][name]
            zeilen.append({"Verfahren": N_REIHE_TEXT[name], "Einstellung": einstellung_text(schluessel[name]), "Plätze (Median)": int(eintrag["n"]),
                           "Kantenzugriffe (Median)": int(round(k["zugriffe"])), "Anteil an 2m": round(k["zugriffe"] / eintrag["vol"], 3),
                           "F1-Median": round(k["median"], 3), "Treffer": f"{k['treffer']} von {k['zahl']}"})
    return zeilen


N_REIHE_TEXT = {"push": "Push (Vorführung)", "push_traege": "Push träge (ACL)", "abgestimmt": "PageRank abgestimmt", "gierig": "gierig abgestimmt",
                "waerme": "Wärmeleitung abgestimmt"}


def verbund_text(daten: dict) -> str:
    r = daten["verbund_reihe"]
    zs = sorted(r)
    zugriffe = [r[z]["zugriffe"] for z in zs]
    schluessel = M.VERBUND_REIHE_SCHLUESSEL
    return (f"**Hallenverbund** (Hallen 8×8, {einstellung_text(schluessel)}, je {r[zs[0]]['zahl']} Startplätze): von {ganz(r[zs[0]]['n'])} bis {ganz(r[zs[-1]]['n'])} "
            f"Plätzen im Median {ganz(min(zugriffe))} bis {ganz(max(zugriffe))} Kantenzugriffe, {min(r[z]['treffer'] for z in zs)} bis {max(r[z]['treffer'] for z in zs)} "
            f"Treffer von {r[zs[0]]['zahl']}.")


FALL_TEXT = {"hallen8": "Hallenverbund 8×8, Hallen 8×8 (64 Starts)", "hallen16": "Hallenverbund 8×8, Hallen 16×16 (256 Starts)",
             "a3_120": "Zufallsgemeinschaften, Außengrad 3, Gruppen zu 120 (60 Netze)", "a3_480": "Zufallsgemeinschaften, Außengrad 3, Gruppen zu 480 (60 Netze)"}


def tabelle_regel(daten: dict, fall: str) -> list:
    r = daten["regel"][fall]
    zeilen = []
    for eps in M.REGEL_EPS:
        for regel in M.REGEL_REGELN:
            k = r[f"{eps:g}|{regel}"]
            zeilen.append({"ε": zahl(eps), "Sweep-Regel": regel_anzeige(regel), "F1-Median": round(k["median"], 3), "F1-Mittel": round(k["mittel"], 3),
                           "Treffer": f"{k['treffer']} von {k['zahl']}", "Plätze im Schnitt (Median)": int(round(k["groesse"])),
                           "Kantenzugriffe (Median)": int(round(k["zugriffe"]))})
    return zeilen


def nur_eps(daten: dict, fall: str = "a3_480") -> dict:
    """Wie weit bewegen Regel bzw. ε den F1-Median bei gleichem β? Je ε die Spanne über die Regeln, je Regel die Spanne über ε."""
    r = daten["regel"][fall]
    ueber_regeln = {eps: [r[f"{eps:g}|{regel}"]["median"] for regel in M.REGEL_REGELN] for eps in M.REGEL_EPS}
    ueber_eps = {regel: [r[f"{eps:g}|{regel}"]["median"] for eps in M.REGEL_EPS] for regel in M.REGEL_REGELN}
    return {"fall": fall, "regel_spanne": max(max(x) - min(x) for x in ueber_regeln.values()),
            "eps_spanne": min(max(x) - min(x) for x in ueber_eps.values()),
            "mediane_min": ueber_eps["min"], "zahl": r[f"{M.REGEL_EPS[0]:g}|min"]["zahl"]}


def verdikt_nur_eps(daten: dict):
    e = nur_eps(daten)
    werte = ", ".join(f"{de(m, 2)} bei ε = {zahl(eps)}" for eps, m in zip(M.REGEL_EPS, e["mediane_min"]))
    text = (f"Gegenbeispiel auf den Zufallsgemeinschaften mit Außengrad 3 (Gruppen zu 480, {e['zahl']} Netze): Die Sweep-Regel verschiebt den F1-Median bei gleichem ε um "
            f"höchstens {de(e['regel_spanne'], 2)}, ε allein dagegen je Regel um mindestens {de(e['eps_spanne'], 2)} („min“: {werte}).")
    return ("info" if e["regel_spanne"] < e["eps_spanne"] else "warning"), text


def gleichstandsbeispiel() -> dict:
    """Hallenverbund 3×3 mit Hallen 6×6, Start (2,2) der mittleren Halle, Budget 400, erstes Tal 0,4: (Plätze, davon aus der Starthalle) je Gleichstandsregel."""
    g = N.hallenverbund(3, 6)
    ziel = N.mittlere_halle(3, 6)
    start = N.hallenknoten(3, 6, 1, 1, 2, 2)
    erg = {}
    for art in ("gierig-grad", "gierig-entdeckt"):
        s = schnitt(g, ziel, start, art, 400, "tal0.4")
        erg[art] = (s.ergebnis.groesse, len(set(s.menge) & ziel))
    return erg


# ----------------------------------------------------------------------------------------------------------------------------------
# Experiment 4: welche Größe findet man?
# ----------------------------------------------------------------------------------------------------------------------------------

def treppe(g: N.Graph, z: int, a: int):
    """Konduktanz einer inneren Halle, zweier Nachbarhallen und eines Blocks 2×2 (exakt als Brüche), mit Randkanten und Volumen."""
    erg = []
    for zeilen, spalten, name in ((1, 1, "1 Halle"), (1, 2, "2 Nachbarhallen"), (2, 2, "Block 2×2")):
        block = N.block_plaetze(z, a, zeilen, spalten)
        rand, vol = W.rand_und_volumen(g, block)
        erg.append({"name": name, "plaetze": len(block), "rand": rand, "volumen": vol, "konduktanz": rand / min(vol, g.vol - vol)})
    return erg


def verdikt_treppe(stufen):
    teile = " > ".join(f"{s['rand']}/{ganz(s['volumen'])}" for s in stufen)
    werte = [s["konduktanz"] for s in stufen]
    if werte[0] > werte[1] > werte[2]:
        return "warning", f"Größere Blöcke haben hier die kleinere Konduktanz ({teile}). Die kleinste Konduktanz allein führt zu größeren Mengen; welche Größe man findet, entscheidet die Größenbegrenzung (ε, Budget, t) oder die Sweep-Regel."
    return "info", f"Konduktanz der drei Blöcke: {teile}."


def verdikt_regel(daten: dict, fall: str, eps: float):
    """Dieselbe PageRank-Rechnung, nur die Sweep-Regel geändert (vorgerechnet, alle Startplätze bzw. 60 Netze)."""
    r = daten["regel"][fall]
    a, b = r[f"{eps:g}|min"], r[f"{eps:g}|tal0.4"]
    text = (f"Dieselbe PageRank-Rechnung (β = {zahl(M.REGEL_BETA)}, ε = {zahl(eps)}), {a['zahl']} Läufe: „min“ findet im Median "
            f"{anzahl(a['groesse'], 'Platz', 'Plätze')} (F1-Median {de(a['median'], 2)}, {a['treffer']} Treffer), „erstes Tal 0,4“ "
            f"{anzahl(b['groesse'], 'Platz', 'Plätze')} (F1-Median {de(b['median'], 2)}, {b['treffer']} Treffer).")
    return ("warning" if abs(a["median"] - b["median"]) > 0.1 else "info"), text


# ----------------------------------------------------------------------------------------------------------------------------------
# Experiment 5: die Gegner
# ----------------------------------------------------------------------------------------------------------------------------------

def zaehlungen(daten: dict) -> dict:
    return {
        "pagerank_tal": M.zaehlung(daten["test"], daten["wahl"], "tal"),
        "pagerank_min": M.zaehlung(daten["test"], daten["wahl"], "min"),
        "waerme": M.zaehlung(daten["test"], daten["wahl"], gegner="waerme"),
    }


def fraktion(anteil: tuple) -> str:
    return f"{anteil[0]} von {anteil[1]}"


def verdikt_gegner(z: dict):
    """Verdikt zur Zählung der gierigen Erweiterung gegen den abgestimmten PageRank-Schnitt mit „erstem Tal“."""
    t = z["treffer_je_familie"]
    gem_min = t["a1"][0] + t["a3"][0]
    gem_n = t["a1"][1] + t["a3"][1]
    n = z["zellen"]
    text = (f"In den {n} Zellen innerhalb der Abstimmbereiche las die auf den Abstimm-Netzen beste gierige Erweiterung in {z['sparsamer']} von {n} Zellen weniger als der "
            f"abgestimmte PageRank-Schnitt mit „erstem Tal“ (PageRank-Zugriffe das {de(z['faktor_min'], 1)}- bis {de(z['faktor_max'], 0)}-Fache). Mindestens so viele Treffer "
            f"hatte sie auf den Zufallsgemeinschaften in {gem_min} von {gem_n} Zellen, auf den Gitterhallen in {fraktion(t['hallen'])}; im Median (zwei Stellen) war sie in "
            f"{z['median']} von {n} Zellen mindestens so gut.")
    if z["sparsamer"] == n and z["faktor_min"] >= 5:
        text += " In jeder Zelle kam sie mit weniger als einem Fünftel der Zugriffe aus."
    return "info", text


def waerme_vergleich(daten: dict) -> dict:
    """Wärmeleitung, beste gierige Variante und PageRank („erstes Tal“) auf den 10 Zellen der Zufallsgemeinschaften innerhalb der Abstimmung."""
    erg = {"zellen": 0, "laeufe": 0, "summe": {"waerme": 0, "gierig": 0, "pagerank": 0}, "waerme_mind_pagerank": 0, "waerme_mehr_als_gierig": 0,
           "gierig_mehr_als_waerme": 0, "waerme_teuerste": 0}
    for familie in ("a1", "a3"):
        gv, gs = M.beste_gierige(daten["wahl"][familie])
        hs_w = M.haupt_sweep(daten["wahl"][familie], "waerme")
        for z in M.GROESSEN_ABST:
            t = daten["test"][familie][z]
            w = t["waerme"][hs_w]
            pr = t["pagerank"]["tal"]
            gi = t[gv][gs]
            erg["zellen"] += 1
            erg["laeufe"] += w["zahl"]
            for name, x in (("waerme", w), ("gierig", gi), ("pagerank", pr)):
                erg["summe"][name] += x["treffer"]
            erg["waerme_mind_pagerank"] += w["treffer"] >= pr["treffer"]
            erg["waerme_mehr_als_gierig"] += w["treffer"] > gi["treffer"]
            erg["gierig_mehr_als_waerme"] += gi["treffer"] > w["treffer"]
            erg["waerme_teuerste"] += w["zugriffe"] >= max(pr["zugriffe"], gi["zugriffe"])
    return erg


def lokalitaet(daten: dict, familie: str, verfahren: str, sweep: str, zellen=None):
    """(kleinstes, größtes) Verhältnis Kantenzugriffe (Median) zu 2m über die Zellen."""
    werte = [daten["test"][familie][z][verfahren][sweep]["zugriffe"] / daten["netze"][familie][z]["vol"] for z in (zellen or M.test_zellen(familie))]
    return min(werte), max(werte)


def verdikt_zuverlaessigkeit(daten: dict, z: dict):
    """Wer zuverlässiger war: nach Netzfamilie getrennt, dazu die Wärmeleitung auf den Zufallsgemeinschaften."""
    t = z["pagerank_tal"]["treffer_je_familie"]
    v = z["pagerank_tal"]["gegner_treffer_vorn_je_familie"]
    gem = (t["a1"][0] + t["a3"][0], t["a1"][1] + t["a3"][1])
    lo, hi = lokalitaet(daten, "hallen", "pagerank", "tal", M.SEITEN_ABST)
    w = waerme_vergleich(daten)
    gemein = sorted({C.VERFAHREN_TEXT[M.beste_gierige(daten["wahl"][f])[0]] for f in ("a1", "a3")})
    hallen = C.VERFAHREN_TEXT[M.beste_gierige(daten["wahl"]["hallen"])[0]]
    text = (f"Wie zuverlässig die gierige Erweiterung war, hängt an Netz und Startregel: Auf den Zufallsgemeinschaften (beste Variante: {', '.join(gemein)}) hatte sie "
            f"in {gem[0]} von {gem[1]} Zellen mindestens so viele Treffer wie PageRank; auf den Gitterhallen (beste Variante: {hallen}) hatte PageRank "
            f"in {v['hallen'][0]} von {v['hallen'][1]} Zellen mehr Treffer, las dabei aber das {de(lo, 1)}- bis {de(hi, 1)}-Fache der Summe aller Grade des Netzes. "
            f"Treffer zusammen über die {w['zellen']} Zellen der Zufallsgemeinschaften ({ganz(w['laeufe'])} Netze): Wärmeleitung {w['summe']['waerme']}, gierig "
            f"{w['summe']['gierig']}, PageRank {w['summe']['pagerank']}. Gegen die gierige Erweiterung hatte die Wärmeleitung in {w['waerme_mehr_als_gierig']} Zellen mehr "
            f"und in {w['gierig_mehr_als_waerme']} weniger Treffer und las in {w['waerme_teuerste']} von {w['zellen']} Zellen von den dreien am meisten.")
    return "info", text


def pagerank_nie_sparsamste(daten: dict) -> int:
    """Zahl der Zellen (innerhalb der Abstimmung), in denen eine PageRank-Einstellung die wenigsten Kantenzugriffe aller Verfahren und Sweep-Familien hat."""
    zahl_ = 0
    for familie in M.FAMILIEN:
        for zz in M.innere_zellen(familie):
            t = daten["test"][familie][zz]
            kleinste = min(t[v][s]["zugriffe"] for v in M.VERFAHREN_VERGLEICH for s in M.SWEEPS)
            zahl_ += min(t["pagerank"][s]["zugriffe"] for s in M.SWEEPS) <= kleinste
    return zahl_


def sparsamste_und_lokal_text(daten: dict) -> str:
    zellen = sum(len(M.innere_zellen(f)) for f in M.FAMILIEN)
    lo_t, hi_t = lokalitaet(daten, "hallen", "pagerank", "tal")
    lo_m, hi_m = lokalitaet(daten, "hallen", "pagerank", "min")
    lo_w, hi_w = lokalitaet(daten, "a3", "waerme", M.haupt_sweep(daten["wahl"]["a3"], "waerme"))
    min_treffer = [daten["test"]["hallen"][a]["pagerank"]["min"]["treffer"] for a in M.SEITEN_TEST]
    min_zahl = [daten["test"]["hallen"][a]["pagerank"]["min"]["zahl"] for a in M.SEITEN_TEST]
    schwach = ", ".join(f"a = {a}: {t} von {n}" for a, t, n in zip(M.SEITEN_TEST, min_treffer, min_zahl) if t < 0.75 * n)
    aussen = {f: daten["test"][f][960] for f in ("a1", "a3")}
    g1, g3 = M.beste_gierige(daten["wahl"]["a1"]), M.beste_gierige(daten["wahl"]["a3"])
    w1, w3 = M.haupt_sweep(daten["wahl"]["a1"], "waerme"), M.haupt_sweep(daten["wahl"]["a3"], "waerme")
    sparsam = pagerank_nie_sparsamste(daten)
    satz = f"in **keiner der {zellen}** Zellen" if sparsam == 0 else f"in **{sparsam} von {zellen}** Zellen"
    v_beta, v_eps = M.PUSH_VORFUEHRUNG
    return (
        f"**Der ehrliche Befund gegen den PageRank:** Seine zwei abgestimmten Einstellungen („erstes Tal“ und „min“) waren {satz} innerhalb der "
        f"Abstimmbereiche das sparsamste Verfahren, verglichen nach den Kantenzugriffen im Median mit den abgestimmten Einstellungen aller Verfahren, "
        f"ohne Blick auf die Treffer. Das ist eine Aussage über diese zwei Einstellungen, nicht über die feste Push-Einstellung aus Experiment 3 "
        f"(β = {zahl(v_beta)}, ε = {zahl(v_eps)}, „min“), für die das „gleich viel“ gemessen ist. Auf den Gitterhallen "
        f"(a = {M.SEITEN_TEST[0]} bis {M.SEITEN_TEST[-1]}) ist die zuverlässige PageRank-Einstellung („erstes Tal“) **nicht lokal**: sie liest das "
        f"{de(lo_t, 1)}- bis {de(hi_t, 1)}-Fache "
        f"der Summe aller Grade. Die sparsame Einstellung mit „min“ liest das {de(lo_m, 2)}- bis {de(hi_m, 2)}-Fache, hat aber auf einzelnen Hallengrößen wenige Treffer ({schwach}). "
        f"Bei Außengrad 3 liest die Wärmeleitung das {de(lo_w, 2)}- bis {de(hi_w, 2)}-Fache.\n\n"
        f"**Außerhalb der Abstimmbereiche** ist das Bild gemischt (Treffer von {M.NETZE_TEST}). Gruppen zu 960, Außengrad 1: gierig {aussen['a1'][g1[0]][g1[1]]['treffer']}, "
        f"PageRank („erstes Tal“) {aussen['a1']['pagerank']['tal']['treffer']}, Wärmeleitung {aussen['a1']['waerme'][w1]['treffer']}. Gruppen zu 960, Außengrad 3: "
        f"{aussen['a3'][g3[0]][g3[1]]['treffer']}, {aussen['a3']['pagerank']['tal']['treffer']} und {aussen['a3']['waerme'][w3]['treffer']}. Gruppen zu 20, Außengrad 3: "
        f"gierig {daten['test']['a3'][20][g3[0]][g3[1]]['treffer']}, PageRank {daten['test']['a3'][20]['pagerank']['tal']['treffer']}."
    )


def tabelle_test(daten: dict, familie: str, zellen=None, sweeps_alle: bool = False):
    """Zeilen für die Anzeige: je Verfahren (Haupteinstellung, auf Wunsch beide Sweep-Familien) je Zelle „Median / Mittel / Treffer“ und Zugriffe."""
    wahl = daten["wahl"][familie]
    zellen = zellen or M.test_zellen(familie)
    zeilen = []
    for v in M.VERFAHREN_VERGLEICH:
        haupt = M.haupt_sweep(wahl, v)
        for s in M.SWEEPS:
            if not sweeps_alle and s != haupt:
                continue
            k = M.schluessel_aus_wahl(v, wahl[v][s])
            zeile = {"Verfahren": C.VERFAHREN_TEXT[v] + (" ★" if s == haupt else ""), "Einstellung": einstellung_text(k)}
            zugriffe = []
            for z in zellen:
                w = daten["test"][familie][z][v][s]
                zeile[str(z) + ("" if z in M.innere_zellen(familie) else " (außerhalb)")] = f"{de(w['median'], 2)} / {de(w['mittel'], 2)} / {w['treffer']}"
                zugriffe.append(w["zugriffe"])
            zeile["Kantenzugriffe (Median je Zelle)"] = f"{ganz(min(zugriffe))} bis {ganz(max(zugriffe))}"
            zeilen.append(zeile)
    return zeilen


def live_vergleich(sz: S.Szenario, wahl: dict):
    """Alle Verfahren mit den abgestimmten Haupteinstellungen der Netzfamilie auf dem aktuellen Netz (nicht auf den Handnetzen)."""
    if sz.familie is None:
        return []
    schluessel = [feste_einstellung(wahl, sz.familie, v) for v in M.VERFAHREN_VERGLEICH]
    erg = laufe(sz.g, sz.ziel, sz.start, schluessel)
    return [{"Verfahren": C.VERFAHREN_TEXT[k[0]], "Einstellung": einstellung_text(k), "F1": round(erg[k].f1, 3), "|S|": erg[k].groesse,
             "Kantenzugriffe": erg[k].zugriffe, "Anteil an 2m": round(erg[k].zugriffe / sz.g.vol, 3)} for k in schluessel]


def fiedler_kennzahlen(daten: dict) -> dict:
    f = daten["fiedler"]
    gemein = [x[0]["f1"] for x in f["gemein"]]
    return {"hallen_f1": max(x["f1"] for x in f["hallen"]), "hallen_abstand": f["hallen"][0]["abstand_ew"], "netze": len(gemein),
            "null": sum(v < 0.01 for v in gemein), "treffer": sum(v >= 0.9 for v in gemein), "hoechstens": max(gemein)}


def fiedler_text(daten: dict) -> str:
    k = fiedler_kennzahlen(daten)
    mantisse, exponent = f"{k['hallen_abstand']:.1e}".split("e")
    hoch = str(int(exponent)).translate(str.maketrans("-0123456789", "⁻⁰¹²³⁴⁵⁶⁷⁸⁹"))
    treffer = "kein Netz war ein Treffer" if k["treffer"] == 0 else f"Treffer: {k['treffer']}"
    return (f"**Bezug: globaler Fiedler-Sweep.** Er sucht die beste Zweiteilung des **ganzen** Netzes, eine andere Frage. Auf dem Hallenverbund 8×8 (Hallen 8×8) hat die "
            f"gefundene Menge zur Starthalle F1 = {de(k['hallen_f1'], 2)}; der zweite und der dritte Eigenwert liegen dort nur {mantisse.replace('.', ',')}·10{hoch} "
            f"auseinander, der Vektor ist also schlecht bestimmt (deshalb steht hier keine Größe der Menge). Auf {k['netze']} Zufallsgemeinschaften mit "
            f"{ganz(M.N_STANDARD)} Plätzen (Gruppen zu 60, Außengrad 1) lag F1 zur Startgruppe in {k['null']} Netzen unter 0,01; der höchste Wert war "
            f"{de(k['hoechstens'], 2)}, {treffer}.")


def gradfalle_hinweis(daten: dict) -> str:
    """Wo bei ε = 10⁻³ der Unterschied verschwindet und wo nicht."""
    def spanne(art):
        d = [sammel_zeile(daten, art, 1e-3, "p/Grad", r)["median"] - sammel_zeile(daten, art, 1e-3, "p", r)["median"] for r in M.SAMMEL_REGELN]
        return max(d)

    a, b = sammel_zeile(daten, "fern200", 1e-3, "p/Grad", "tal0.05"), sammel_zeile(daten, "fern200", 1e-3, "p", "tal0.05")
    return (f"Bei den fünf nahen Sammelpunkten und ε = 0,001 liegt der Median nach p/Grad mit allen vier Regeln höchstens {de(spanne('nah'), 3)} höher; bei 200 fernen "
            f"Sammelpunkten und „erstem Tal“ mit Schwelle 0,05 bleibt der Unterschied auch bei ε = 0,001 groß ({de(a['median'], 3)} gegen {de(b['median'], 3)}).")


def netzgroessen_text(daten: dict, familie: str) -> str:
    """Summe aller Grade (2m) je Zelle, zum Einordnen der Kantenzugriffe."""
    werte = daten["netze"][familie]
    if familie == "hallen":
        return "Summe aller Grade (2m) im Verbund 8×8: " + ", ".join(f"a = {z}: {ganz(werte[z]['vol'])}" for z in sorted(werte)) + "."
    mitte = [werte[z]["vol"] for z in sorted(werte)]
    return f"Summe aller Grade (2m) der Netze mit {ganz(M.N_STANDARD)} Plätzen (Median je Zelle): {ganz(min(mitte))} bis {ganz(max(mitte))}."


# ----------------------------------------------------------------------------------------------------------------------------------
# Gütezusage von Andersen, Chung und Lang
# ----------------------------------------------------------------------------------------------------------------------------------

def acl_schranke(phi: float, volumen: int):
    """Mit α = 10·Φ(C): (α, √(90·α·ln(30·√vol C))), die Schranke aus dem Beweis von Satz 5 (natürlicher Logarithmus)."""
    alpha = 10 * phi
    return alpha, math.sqrt(90 * alpha * math.log(30 * math.sqrt(volumen)))


def acl_beispiel() -> dict:
    """Die Starthalle 8×8 im Hallenverbund 8×8 und das Handnetz."""
    g = N.hallenverbund(8, 8)
    halle = N.mittlere_halle(8, 8)
    rand, vol = W.rand_und_volumen(g, halle)
    phi = rand / vol
    alpha, schranke = acl_schranke(phi, vol)
    hand = N.handnetz()
    kleinste = min(
        W.konduktanz(hand, s) for k in range(1, hand.n) for s in combinations(range(hand.n), k) if 3 * sum(hand.d[u] for u in s) <= 2 * hand.vol)
    return {"phi": phi, "rand": rand, "vol": vol, "alpha": alpha, "schranke": schranke, "hand_kleinste": kleinste, "teil_anteil": vol / g.vol}


def acl_text() -> str:
    b = acl_beispiel()
    return (f"**Auf Vorführgröße ist die Zusage leer.** Für die Starthalle 8×8 ($\\Phi = {b['rand']}/{b['vol']}$, Volumen {b['vol']}) und $\\alpha = 10\\,\\Phi$ "
            f"= {de(b['alpha'], 3)} liefert die Formel rund **{de(b['schranke'], 1)}**. Die Konduktanz ist aber nie größer als 1 (die Randverbindungen sind höchstens so viele "
            f"wie das kleinere Volumen): Die Zusage sagt hier nichts. Auf dem Handnetz ist die Voraussetzung gar nicht erfüllbar: Keine Menge mit höchstens zwei Dritteln "
            f"des Volumens hat $\\Phi \\le 1/10$ (die kleinste ist {b['hand_kleinste']}).")
