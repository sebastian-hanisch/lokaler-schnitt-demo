"""Verdikte an von Hand gesetzten Werten: Schwellen, Art und jede Zahl im Text."""

import types

import lsn_evaluation as E
import lsn_messen as M
from lsn_verfahren import Ergebnis, Schnitt


def _schnitt(f1, groesse, phi=0.1, zugriffe=100):
    return Schnitt(Ergebnis(f1, zugriffe, groesse), tuple(range(groesse)), tuple(range(groesse)), (phi,) * groesse, phi, {}, zugriffe)


def _sz(ziel=10, vol=1000, netz="hallen", rand=0):
    """Die ersten `rand` Plätze der Zielmenge haben je eine Verbindung nach außen; jeder Zielplatz hat den Grad 10."""
    nb = [[ziel] if u < rand else [] for u in range(ziel)]
    return types.SimpleNamespace(ziel=frozenset(range(ziel)), netz=netz, g=types.SimpleNamespace(vol=vol, nb=nb, d=[10] * ziel), start=0)


def test_verdikt_ergebnis_groesser_sagt_nur_was_die_konduktanz_zeigt():
    sz = _sz(rand=20 // 2)                                                         # gepflanzt: Rand 10, Volumen 100, Konduktanz 0,1
    besser = E.verdikt_ergebnis(_schnitt(0.3, 16, phi=0.05), sz, "X")[1]
    assert "deutlich größer" in besser and "nicht schlechter" in besser and "0,1000" in besser
    gleich = E.verdikt_ergebnis(_schnitt(0.3, 16, phi=0.1), sz, "X")[1]
    assert "nicht schlechter" in gleich
    schlechter = E.verdikt_ergebnis(_schnitt(0.3, 16, phi=0.3), sz, "X")[1]
    assert "Auch nach der Konduktanz ist sie schlechter" in schlechter and "0,1000" in schlechter and "nicht schlechter" not in schlechter
    knapp = E.verdikt_ergebnis(_schnitt(0.3, 16, phi=0.100001), sz, "X")[1]
    assert "auf vier Stellen gleich" in knapp and "schlechter" not in knapp
    for text in (besser, gleich, schlechter, knapp):
        assert "nicht falsch" not in text


def test_einzahl_bei_einem_platz():
    assert "X findet 1 Platz (gepflanzt: 10)" in E.verdikt_ergebnis(_schnitt(0.1, 1), _sz(), "X")[1]
    assert "a: 1 Platz (F1 0,10)" in E.verdikt_ordnung_und_regel([("a", Ergebnis(0.1, 1, 1)), ("b", Ergebnis(0.1, 1, 2))], 3)[1]
    assert (E.anzahl(1, "Push", "Pushes"), E.anzahl(8, "Push", "Pushes"), E.anzahl(1000, "Platz", "Plätze")) == ("1 Push", "8 Pushes", "1 000 Plätze")


def test_verdikt_ordnung_und_regel_nennt_nur_groesse_und_f1():
    text = E.verdikt_ordnung_und_regel([("a", Ergebnis(0.08, 1, 471)), ("b", Ergebnis(0.08, 1, 471)), ("c", Ergebnis(0.05, 1, 385))], 480)[1]
    assert "fast dasselbe" not in text and "in Größe und F1 ähnlich" in text and "1,5-Fache" in text and "höchstens 0,1" in text


def test_verdikt_ergebnis_treffer_ab_0_9_einschliesslich():
    art, text = E.verdikt_ergebnis(_schnitt(0.9, 11, phi=0.0123), _sz(), "X")
    assert art == "success" and "X findet 11 Plätze (gepflanzt: 10), F1 = 0,90, Konduktanz 0,0123." in text and "Treffer" in text
    assert E.verdikt_ergebnis(_schnitt(0.899, 11), _sz(), "X")[0] == "warning"


def test_verdikt_ergebnis_groesser_kleiner_aehnlich():
    assert "deutlich größer" in E.verdikt_ergebnis(_schnitt(0.3, 16), _sz(), "X")[1]      # 16 > 15
    assert "Größe ähnlich" in E.verdikt_ergebnis(_schnitt(0.3, 15), _sz(), "X")[1]       # genau das 1,5-Fache
    assert "deutlich kleiner" in E.verdikt_ergebnis(_schnitt(0.3, 6), _sz(), "X")[1]     # 6 < 10/1,5


def test_verdikt_aufwand_schwelle_halbes_netz():
    art, text = E.verdikt_aufwand(_schnitt(1, 5, zugriffe=499), _sz(vol=1000), "X")
    assert art == "success" and "499 Kantenzugriffe" in text and "0,50-mal" in text and "lokal" in text
    art, text = E.verdikt_aufwand(_schnitt(1, 5, zugriffe=500), _sz(vol=1000), "X")
    assert art == "warning" and "nicht lokal" in text


def test_verdikt_neustart_nennt_16_neunzehntel_nur_auf_dem_handfall():
    n = E.Neustart(None, 16 / 19, (), ())
    art, text = E.verdikt_neustart(_sz(netz="hand"), 0.25, n)
    assert art == "info" and "**84,2 %**" in text and "16/19" in text and "Starthalle" in text
    assert "16/19" not in E.verdikt_neustart(_sz(netz="hand"), 0.1, n)[1]
    assert "Zielgruppe" in E.verdikt_neustart(_sz(netz="gemein"), 0.1, n)[1]


def test_verdikt_anteil_gemessen_success_nur_wenn_bei_allen():
    anteil = {"betas": [0.5, 0.001], "median": [0.9, 0.2], "monoton": 64, "starts": 64}
    art, text = E.verdikt_anteil_gemessen(anteil)
    assert art == "success" and "bei 64 von 64 Startplätzen" in text and "von 90,0 % auf 20,0 %" in text
    anteil["monoton"] = 63
    assert E.verdikt_anteil_gemessen(anteil)[0] == "info"


def test_verdikt_ordnung_und_regel_schwellen():
    gleich = [("a", Ergebnis(0.99, 1, 60)), ("b", Ergebnis(0.99, 1, 61))]
    assert E.verdikt_ordnung_und_regel(gleich, 60)[0] == "info"
    anders = [("a", Ergebnis(0.99, 1, 60)), ("b", Ergebnis(0.80, 1, 61))]
    art, text = E.verdikt_ordnung_und_regel(anders, 60)
    assert art == "warning" and "a: 60 Plätze (F1 0,99)" in text and "entscheiden" in text
    assert E.verdikt_ordnung_und_regel([("a", Ergebnis(0.5, 1, 100)), ("b", Ergebnis(0.5, 1, 60))], 60)[0] == "warning"


def _zeile(median, mittel, sammel=0.0, zahl=96):
    return {"f1": [median] * zahl, "median": median, "mittel": mittel, "sammel_mittel": sammel}


def test_verdikt_gradfalle_vier_zweige():
    art, text = E.verdikt_gradfalle(_zeile(0.98, 0.96), _zeile(0.31, 0.42, sammel=1.5), "nah", 3e-4, "tal0.2")
    assert art == "warning" and "nach p/Grad 0,980, nach p allein 0,310" in text and "1,50 Sammelpunkte" in text and "96 Netze" in text
    art, text = E.verdikt_gradfalle(_zeile(0.98, 0.97), _zeile(0.95, 0.85), "fern40", 3e-4, "min")
    assert art == "warning" and "im Mittel nicht" in text
    art, text = E.verdikt_gradfalle(_zeile(0.80, 0.80), _zeile(0.90, 0.90), "ohne", 1e-3, "min")
    assert art == "info" and "schadet die Ordnung ohne Division nicht" in text
    art, text = E.verdikt_gradfalle(_zeile(0.97, 0.95), _zeile(0.96, 0.94), "nah", 1e-3, "min")
    assert art == "info" and "höchstens 0,05" in text


def _n_reihe(push, vol, gierig=(5000, 5000, 5000, 5000), waerme=(1, 2, 3, 40)):
    erg = {}
    for i, n in enumerate((960, 4000, 16000, 64000)):
        erg[n] = {"vol": vol[i], "n": n, "kurven": {"push": {"zugriffe": push[i]}, "gierig": {"zugriffe": gierig[i]}, "waerme": {"zugriffe": waerme[i]}}}
    return erg


def test_verdikt_gleich_viel_schwelle_15_prozent():
    r = _n_reihe((15000, 1000, 1100, 1150), (8000, 36000, 140000, 580000))
    art, text = E.verdikt_gleich_viel(r, 0.006, 3e-4)
    assert art == "success" and "1 000 bis 1 150" in text and "1,88-mal" in text and "555 556" in text
    assert "gierige Erweiterung" in text and "Wärmeleitung" not in text
    r = _n_reihe((15000, 1000, 1100, 1151), (8000, 36000, 140000, 580000), gierig=(1, 1, 1, 2))
    art, text = E.verdikt_gleich_viel(r, 0.006, 3e-4)
    assert art == "warning" and "gierige" not in text


def test_verdikt_treppe():
    stufen = [{"rand": 4, "volumen": 228, "konduktanz": 4 / 228}, {"rand": 6, "volumen": 456, "konduktanz": 6 / 456}, {"rand": 8, "volumen": 912, "konduktanz": 8 / 912}]
    art, text = E.verdikt_treppe(stufen)
    assert art == "warning" and "4/228 > 6/456 > 8/912" in text
    assert E.verdikt_treppe(list(reversed(stufen)))[0] == "info"


def test_verdikt_regel_schwelle():
    k = lambda med, gr, tr: {"zahl": 64, "median": med, "groesse": gr, "treffer": tr}
    daten = {"regel": {"x": {"0.0003|min": k(0.4, 264, 27), "0.0003|tal0.4": k(0.99, 65, 60)}}}
    art, text = E.verdikt_regel(daten, "x", 3e-4)
    assert art == "warning" and "264 Plätze" in text and "65 Plätze" in text and "64 Läufe" in text and "ε = 0,0003" in text
    daten["regel"]["x"]["0.0003|tal0.4"] = k(0.45, 65, 30)
    assert E.verdikt_regel(daten, "x", 3e-4)[0] == "info"


def _z(sparsamer=14, faktor_min=5.6, hallen=(0, 4), median=13):
    return {"zellen": 14, "sparsamer": sparsamer, "faktor_min": faktor_min, "faktor_max": 167.0, "median": median,
            "treffer_je_familie": {"a1": (5, 5), "a3": (4, 5), "hallen": hallen}}


def test_verdikt_gegner_zahlen_und_fuenftel_satz():
    art, text = E.verdikt_gegner(_z())
    assert art == "info" and "14 von 14 Zellen" in text and "5,6- bis 167-Fache" in text
    assert "in 9 von 10 Zellen" in text and "Gitterhallen in 0 von 4" in text and "13 von 14" in text
    assert "weniger als einem Fünftel" in text
    assert "weniger als einem Fünftel" not in E.verdikt_gegner(_z(faktor_min=4.99))[1]
    assert "weniger als einem Fünftel" not in E.verdikt_gegner(_z(sparsamer=13))[1]


def test_zaehlung_zaehlt_von_hand():
    """Zwei gierige Fassungen, ein Gegner, zwei Zellen je Familie: jede Zählregel an gesetzten Werten."""
    k = lambda median, mittel, treffer, zugriffe: {"median": median, "mittel": mittel, "treffer": treffer, "zugriffe": zugriffe}
    wahl_fam = {v: {s: {"abst_mittel": 0.5} for s in M.SWEEPS} for v in M.VERFAHREN_VERGLEICH}
    wahl_fam["gierig-nachbar"]["tal"]["abst_mittel"] = 0.9           # die beste gierige Einstellung
    wahl = {f: wahl_fam for f in M.FAMILIEN}
    test = {}
    for f in M.FAMILIEN:
        test[f] = {}
        for z in M.innere_zellen(f):
            test[f][z] = {v: {s: k(0.0, 0.0, 0, 10 ** 6) for s in M.SWEEPS} for v in M.VERFAHREN_VERGLEICH}
            # gierig: Median 0,986 (gerundet 0,99), Mittel 0,95, 30 Treffer, 1000 Zugriffe
            test[f][z]["gierig-nachbar"]["tal"] = k(0.986, 0.95, 30, 1000)
            # PageRank: Median 0,994 (gerundet 0,99), Mittel 0,92, 31 Treffer in den Hallen, sonst 30, 8000 Zugriffe
            test[f][z]["pagerank"]["tal"] = k(0.994, 0.92, 31 if f == "hallen" else 30, 8000)
    z = M.zaehlung(test, wahl, "tal")
    zellen = sum(len(M.innere_zellen(f)) for f in M.FAMILIEN)
    assert zellen == 14 and z["zellen"] == 14
    assert z["median"] == 14 and z["treffer"] == 10 and z["sparsamer"] == 14
    assert z["vorn"] == 14 and z["zurueck"] == 0                      # 0,95 > 0,92 + 0,02
    assert z["faktor_min"] == 8 and z["faktor_max"] == 8
    assert z["treffer_je_familie"] == {"a1": (5, 5), "a3": (5, 5), "hallen": (0, 4)}
    assert z["gegner_treffer_vorn_je_familie"]["hallen"] == (4, 4)


def test_zaehle_gradfalle():
    daten = {"sammel": {art: {} for art in M.SAMMEL_ARTEN}}
    for art in ("nah", "fern40", "fern200"):
        for eps in M.SAMMEL_EPS:
            for regel in M.SAMMEL_REGELN:
                daten["sammel"][art][f"{eps:g}|p/Grad|{regel}"] = {"median": 0.9}
                daten["sammel"][art][f"{eps:g}|p|{regel}"] = {"median": 0.9}
    daten["sammel"]["nah"]["0.0001|p|min"]["median"] = 0.5
    daten["sammel"]["fern40"]["0.001|p|tal0.2"]["median"] = 0.96
    daten["sammel"]["fern200"]["0.001|p|tal0.2"]["median"] = 0.85          # Unterschied 0,05: zählt nicht
    assert E.zaehle_gradfalle(daten) == (36, 1, 1)


def test_formatierung():
    assert E.ganz(1234567) == "1 234 567" and E.de(0.5, 2) == "0,50" and E.de(0.4, 2, kurz=True) == "0,4"
    assert E.zahl(1.5e-5) == "0,000015" and E.zahl(0.25) == "0,25"
    assert E.regel_anzeige("min") == "„min“" and E.regel_anzeige("tal0.4") == "„erstes Tal“ mit Schwelle 0,4"
    assert E.einstellung_text(("pagerank", (0.006, 0.001), "min")) == "β = 0,006, ε = 0,001, „min“"
    assert E.einstellung_text(("gierig-nachbar", 6500, "tal0.1")) == "B = 6 500, „erstes Tal“ mit Schwelle 0,1"
    assert E.einstellung_text(("waerme", [20, 3e-5], "min")).startswith("t = 20, δ = 0,00003")
