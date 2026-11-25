"""Regler-Grenzen und Stufen, Netzfamilien, Farben und Presets."""

NETZ_HAND, NETZ_SAMMEL, NETZ_HALLEN, NETZ_GEMEIN, NETZ_NADELN = "hand", "sammel", "hallen", "gemein", "gemein_sammel"
NETZE = (NETZ_HAND, NETZ_SAMMEL, NETZ_HALLEN, NETZ_GEMEIN, NETZ_NADELN)
NETZ_TEXT = {
    NETZ_HAND: "Handnetz „zwei Hallen“",
    NETZ_SAMMEL: "Halle mit Sammelpunkt (von Hand)",
    NETZ_HALLEN: "Hallenverbund",
    NETZ_GEMEIN: "Zufallsgemeinschaften",
    NETZ_NADELN: "Zufallsgemeinschaften mit Sammelpunkten",
}

# Hallenverbund z×z mit Hallen a×a. Größtes Netz am Rand: 16²·20² = 102 400 Plätze (Netzbau und Rechnung je unter 1 s, gemessen).
A_STUFEN = (4, 6, 8, 10, 12, 16, 20)
Z_STUFEN = (4, 8, 16)
# Zufallsgemeinschaften. Größtes Netz: 16 000 Plätze (Bau unter 0,3 s).
GROESSE_STUFEN = (20, 30, 60, 120, 240, 480, 960)
N_STUFEN = (960, 4000, 16000)
AUSSEN_STUFEN = (1, 3)
SAMMEL_ARTEN_APP = ("nah", "fern40", "fern200")
SAMMEL_TEXT = {
    "ohne": "ohne Sammelpunkte",
    "nah": "5 nahe (je 12 Verbindungen in die Zielgruppe, 300 nach außen)",
    "fern40": "40 ferne mit je 400 Verbindungen",
    "fern200": "200 ferne mit je 100 Verbindungen",
}

# Die Arbeit des Push ist durch 1/(β·ε) beschränkt; am Rand (β = 0,00075, ε = 1,5·10⁻⁵) auf dem großen Hallenverbund rund 13 Mio. Kantenzugriffe (rund 3 s).
BETA_STUFEN = (0.00075, 0.0015, 0.003, 0.006, 0.015, 0.04, 0.1, 0.25, 0.5)
EPS_STUFEN = (1.5e-5, 3e-5, 6e-5, 1e-4, 2e-4, 3e-4, 5e-4, 1e-3, 3e-3, 1e-2, 0.05)
GAMMA_STUFEN = (0.02, 0.05, 0.1, 0.2, 0.4, 0.8, 1.6)
BUDGET_STUFEN = (14, 40, 100, 300, 450, 600, 1000, 1500, 2200, 3300, 5000, 6500, 10000, 14000, 20000, 28000)
REGELN = ("min", "tal")
REGEL_TEXT = {"min": "kleinste Konduktanz (min)", "tal": "erstes Tal"}
VERFAHREN_APP = ("pagerank", "gierig", "waerme", "bfs")
VERFAHREN_TEXT = {
    "pagerank": "PageRank (Push) mit Sweep",
    "pagerank-traege": "PageRank träge (ACL-Fassung)",
    "gierig": "gierige Erweiterung",
    "gierig-entdeckt": "gierig, Gleichstand „zuerst entdeckt“",
    "gierig-nachbar": "gierig mit Nachbarschafts-Start",
    "gierig-grad": "gierig, Gleichstand „kleinerer Grad“",
    "waerme": "Wärmeleitung mit Sweep",
    "bfs": "Breitensuche-Kugel mit Sweep",
}
GIERIG_TEXT = {"gierig-entdeckt": "Gleichstand: zuerst entdeckt", "gierig-nachbar": "Nachbarschafts-Start", "gierig-grad": "Gleichstand: kleinerer Grad, dann Nummer"}
HALLEN_STARTS = ("mitte", "ecke", "tuer", "zufall")
HALLEN_START_TEXT = {"mitte": "Mitte der mittleren Halle", "ecke": "Ecke der mittleren Halle", "tuer": "an einer Tür der mittleren Halle", "zufall": "zufälliger Platz der mittleren Halle (Zufalls-Seed)"}

SEED_MAX = 999999
DEFAULT_SEED = 4207

COLOR_MENGE = "#d1495b"
COLOR_ZIEL = "#2F6B65"
COLOR_SAMMEL = "#e69f00"
COLOR_GRAU = "rgba(150,150,150,0.55)"
COLOR_LINIE = "#4c78a8"
COLOR_VERFAHREN = {
    "push": "#4c78a8", "push_traege": "#9ecae9", "abgestimmt": "#1f3b5c", "gierig": "#d1495b", "waerme": "#e69f00",
}


def _preset(netz, **weitere):
    basis = {"netz": netz, "a": 8, "z": 8, "groesse": 60, "aussen": 1, "n": 16000, "sammelart": "nah", "start_platz": 0, "start_halle": "mitte",
             "beta": 0.006, "eps": 3e-4, "verfahren": "pagerank", "regel": "tal", "gamma": 0.4, "gierig_art": "gierig-entdeckt", "budget": 1500,
             "seed": DEFAULT_SEED}
    basis.update(weitere)
    return basis


PRESETS = {
    "Von Hand: Neustart auf zwei Hallen": _preset(NETZ_HAND, beta=0.25, eps=0.05, regel="min", budget=14, gierig_art="gierig-entdeckt"),
    "Falle: Sammelpunkt": _preset(NETZ_NADELN, eps=3e-4, regel="tal", gamma=0.2),
    "Hallenverbund 8×8": _preset(NETZ_HALLEN, eps=3e-4, regel="tal", gamma=0.4),
    "Welche Größe?": _preset(NETZ_HALLEN, eps=3e-4, regel="min"),
    "Unbekannte Größe, Außengrad 3": _preset(NETZ_GEMEIN, groesse=480, aussen=3, beta=0.006, eps=1e-4, regel="min"),
}
PRESET_HELP = {
    "Von Hand: Neustart auf zwei Hallen": "Sechs Plätze, β = 1/4, ε = 1/20: der Push lässt sich Schritt für Schritt nachrechnen.",
    "Falle: Sammelpunkt": "Fünf Plätze mit sehr vielen Verbindungen nah am Start: Was passiert ohne die Division durch den Grad?",
    "Hallenverbund 8×8": "64 Hallen zu je 64 Plätzen, erstes Tal mit Schwelle 0,4.",
    "Welche Größe?": "Dieselbe Rechnung wie „Hallenverbund 8×8“, nur mit der Sweep-Regel „min“.",
    "Unbekannte Größe, Außengrad 3": "Gruppen zu 480 Plätzen mit mehr Verbindungen nach außen.",
}
