"""Jede README-Zahl: (1) jede Tabellenzeile steht wörtlich in der README, aus der Ergebnisdatei gebildet; (2) Stichproben der Ergebnisdatei werden aus dem Code
nachgerechnet (die Netze sind durch SplitMix64 mit ganzzahligen Schwellen plattformgleich; Mittelwerte mit Toleranz, Fiedler als Band); (3) Sätze der README mit
Zahlen werden gegen dieselben Auswertungsfunktionen geprüft, die auch die App benutzt."""

import re
from fractions import Fraction
from pathlib import Path

import pytest

import lsn_daten as D
import lsn_evaluation as E
import lsn_messen as M
import lsn_netze as N
import lsn_sweep as W
from lsn_diffusion import ppr_exakt, push
from lsn_fiedler import fiedler_sweep
from lsn_verfahren import kennzahlen, laufe, median
from readme_zeilen import alle_zeilen

ROOT = Path(__file__).resolve().parent.parent
README = (ROOT / "README.md").read_text(encoding="utf-8")


@pytest.fixture(scope="module")
def daten():
    return D.laden()


def _gleich(neu: dict, alt: dict):
    assert neu["zahl"] == alt["zahl"] and neu["treffer"] == alt["treffer"]
    assert neu["zugriffe"] == pytest.approx(alt["zugriffe"], rel=1e-6) and neu["groesse"] == pytest.approx(alt["groesse"], rel=1e-6)
    assert neu["median"] == pytest.approx(alt["median"], abs=1e-6) and neu["mittel"] == pytest.approx(alt["mittel"], abs=1e-6)


def test_jede_tabellenzeile_steht_in_der_readme(daten):
    fehlt = [z for z in alle_zeilen(daten) if z not in README]
    assert not fehlt, f"{len(fehlt)} Zeilen fehlen, erste: {fehlt[:3]}"
    assert len(alle_zeilen(daten)) > 90


def test_die_annahmen_stehen_gleich_in_app_und_readme():
    assert E.ANNAHMEN_MARKDOWN in README


# ----------------------------------------------------------------------------------------------------------------------------------
# Handrechnungen und Sätze aus dem Bau
# ----------------------------------------------------------------------------------------------------------------------------------

def test_handnetz_zahlen():
    g = N.handnetz()
    p = ppr_exakt(g, 0, 0.25)
    assert [round(float(x) * 627) for x in p[:2]] == [244, 130] and p[:3].sum() == pytest.approx(16 / 19, abs=1e-12)
    _, _, z, pushes = push(g, 0, 0.25, 0.05)
    assert (pushes, z, 1 / (0.25 * 0.05)) == (8, 19, 80)
    assert W.konduktanz(g, {0, 1, 2}) == Fraction(1, 7)
    # ohne Sammelpunkt finden beide Ordnungen die Halle
    werte = {u: float(x) for u, x in enumerate(p)}
    for normiert in (True, False):
        reihe = W.reihe_nach(g, werte, normiert=normiert)
        assert set(reihe[: W.waehle(W.kurve(g, reihe)[0], "min")]) == {0, 1, 2}
    s = N.halle_mit_sammelpunkt()
    assert (W.konduktanz(s, {0, 1, 2}), W.konduktanz(s, {0, 1, 2, 6})) == (Fraction(1, 3), Fraction(2, 5))
    assert "(244/627, 130/627, 14/57, 5/57, 2/57, 2/57)" in README and "8 Pushes" in README and "19 Kantenzugriffe (Obergrenze 80)" in README


def test_gleichstandsbeispiel_und_treppe():
    assert E.gleichstandsbeispiel() == {"gierig-grad": (54, 18), "gierig-entdeckt": (36, 36)}
    d = D.laden()["test"]["hallen"]                                     # App-Satz in Experiment 4
    assert {E.de(d[a]["gierig-grad"]["tal"]["median"], 2) for a in M.SEITEN_TEST} == {"0,67"}
    stufen = E.treppe(N.hallenverbund(8, 8), 8, 8)
    assert [(s["rand"], s["volumen"]) for s in stufen] == [(4, 228), (6, 456), (8, 912)]
    assert "54 Plätze, davon 18 aus der Starthalle" in README and "die Halle (36 von 36)" in README
    assert "eine Halle 4/228, zwei Nachbarhallen 6/456, Block 2×2 8/912" in README


def test_guetezusage():
    b = E.acl_beispiel()
    assert (b["rand"], b["vol"], b["hand_kleinste"]) == (4, 228, Fraction(1, 7))
    assert b["schranke"] == pytest.approx(9.83, abs=0.005) and "**9,8**" in README


# ----------------------------------------------------------------------------------------------------------------------------------
# Anteil gegen β
# ----------------------------------------------------------------------------------------------------------------------------------

def test_anteil_in_der_starthalle_neu_gerechnet(daten):
    g = N.hallenverbund(M.ANTEIL_Z, M.ANTEIL_A)
    ziel = sorted(N.mittlere_halle(M.ANTEIL_Z, M.ANTEIL_A))
    betas = daten["anteil"]["betas"]
    assert tuple(betas) == M.ANTEIL_BETAS
    reihen = [[float(ppr_exakt(g, s, b)[ziel].sum()) for s in ziel] for b in betas]
    monoton = sum(all(reihen[j][i] > reihen[j + 1][i] for j in range(len(betas) - 1)) for i in range(len(ziel)))
    assert monoton == daten["anteil"]["monoton"] == 64
    assert [median(r) for r in reihen] == pytest.approx(daten["anteil"]["median"], abs=1e-8)
    assert E.de(100 * daten["anteil"]["median"][0], 1) == "99,7" and E.de(100 * daten["anteil"]["median"][-1], 1) == "13,4"
    assert "**64 von 64**" in README and "**99,7 % auf 13,4 %**" in README


# ----------------------------------------------------------------------------------------------------------------------------------
# Test- und Abstimmzellen
# ----------------------------------------------------------------------------------------------------------------------------------

@pytest.mark.parametrize("familie, zelle", [("hallen", 6), ("hallen", 8), ("a1", 60), ("a3", 30)])
def test_testzelle_neu_gerechnet(daten, familie, zelle):
    wahl = daten["wahl"][familie]
    keys = M.test_schluessel(wahl)
    ergebnisse = {(zelle, i): laufe(*M.test_fall(familie, zelle, i), keys) for i in M.test_nummern(familie, zelle)}
    neu = M.zellen_kennzahlen(ergebnisse, wahl, (zelle,))[zelle]
    for v in M.VERFAHREN_VERGLEICH:
        for s in M.SWEEPS:
            _gleich(neu[v][s], daten["test"][familie][zelle][v][s])


@pytest.mark.parametrize("familie", ["hallen", "a1"])
def test_abstimmwert_der_gewaehlten_einstellungen_neu_gerechnet(daten, familie):
    wahl = daten["wahl"][familie]
    keys = M.test_schluessel(wahl)
    ergebnisse = {(z, i): laufe(*bau(), keys) for z, i, bau in M.abstimm_faelle(familie)}
    zellen = M.innere_zellen(familie)
    for v in M.VERFAHREN_VERGLEICH:
        for s in M.SWEEPS:
            k = M.schluessel_aus_wahl(v, wahl[v][s])
            mittel = sum(sum(ergebnisse[(z, i)][k].f1 for (zz, i) in ergebnisse if zz == z) / sum(zz == z for zz, _ in ergebnisse) for z in zellen) / len(zellen)
            assert mittel == pytest.approx(wahl[v][s]["abst_mittel"], abs=1e-9), (v, s)
            assert wahl[v][s]["abst_mittel"] >= wahl[v][s]["abst_hoechstwert"] - M.TOLERANZ_WAHL - 1e-12
            assert wahl[v][s]["rand"] == M.am_rand(v, k[1])


def test_raender_wie_in_den_grenzen(daten):
    am_rand = sorted((f, v, s, tuple(w["rand"])) for f in M.FAMILIEN for v, zs in daten["wahl"][f].items() for s, w in zs.items() if w["rand"])
    assert am_rand == [("a3", "waerme", "min", ("delta",)), ("a3", "waerme", "tal", ("delta",)), ("hallen", "gierig-grad", "min", ("B",)),
                       ("hallen", "pagerank", "min", ("eps",)), ("hallen", "waerme", "tal", ("t",))]


def test_netzgroessen(daten):
    for fam, text in (("a1", "137 349 bis 143 930"), ("a3", "165 942 bis 175 960")):
        assert text in E.netzgroessen_text(daten, fam) and text in README
    assert daten["netze"]["hallen"][6]["vol"] == N.hallenverbund(8, 6).vol == 7904
    assert daten["netze"]["hallen"][20]["vol"] == N.hallenverbund(8, 20).vol == 97504


# ----------------------------------------------------------------------------------------------------------------------------------
# Zusatzmessungen
# ----------------------------------------------------------------------------------------------------------------------------------

def test_netzgroesse_4000_neu_gerechnet(daten):
    schluessel = M.n_reihe_schluessel(daten["wahl"]["a1"])
    ergebnisse = [laufe(*M.n_reihe_fall(4000, i), list(schluessel.values())) for i in range(M.N_REIHE_NETZE)]
    for name, k in schluessel.items():
        _gleich(kennzahlen([e[k] for e in ergebnisse]), daten["n_reihe"][4000]["kurven"][name])


def test_saetze_zur_netzgroesse(daten):
    r = daten["n_reihe"]
    verhaeltnis = [r[n]["kurven"]["push_traege"]["zugriffe"] / r[n]["kurven"]["push"]["zugriffe"] for n in M.N_REIHE]
    assert (E.de(min(verhaeltnis), 1), E.de(max(verhaeltnis), 1)) == ("1,8", "2,2") and "1,8- bis 2,2-Fache" in README
    assert min(k["median"] for n in M.N_REIHE for k in r[n]["kurven"].values()) >= 0.99
    assert r[960]["kurven"]["push"]["zugriffe"] > r[960]["vol"]
    assert round(r[960]["kurven"]["abgestimmt"]["zugriffe"] / r[960]["vol"]) == 67 and "das 67-Fache" in README
    for name in ("push", "gierig", "waerme"):
        klein, gross = E.gleich_viel(r, name, 4000)
        assert gross <= 1.15 * klein, name
    assert E.ganz(1 / (0.006 * 3e-4)) == "555 556" and "555 556" in README


@pytest.mark.parametrize("z", [4, 8])
def test_verbundreihe_neu_gerechnet(daten, z):
    ergebnisse = [laufe(netz, ziel, s, [M.VERBUND_REIHE_SCHLUESSEL])[M.VERBUND_REIHE_SCHLUESSEL] for netz, ziel, s in M.verbund_reihe_faelle(z)]
    _gleich(kennzahlen(ergebnisse), daten["verbund_reihe"][z])


@pytest.mark.parametrize("art, eps", [("nah", 3e-4), ("fern200", 1e-3)])
def test_gradfalle_neu_gerechnet(daten, art, eps):
    werte = {(o, r): [] for o in M.ORDNUNGEN for r in M.SAMMEL_REGELN}
    for i in range(M.SAMMEL_NETZE):
        g, ziel, s, sammel = M.sammel_fall(art, i)
        p, *_ = push(g, s, M.SAMMEL_BETA, eps)
        for ordnung in M.ORDNUNGEN:
            reihe = W.reihe_nach(g, p, normiert=ordnung == "p/Grad")
            phis, _ = W.kurve(g, reihe)
            for regel in M.SAMMEL_REGELN:
                menge = reihe[: W.waehle(phis, regel)]
                werte[(ordnung, regel)].append((W.f1_menge(menge, ziel), len(sammel & set(menge))))
    for (ordnung, regel), w in werte.items():
        alt = E.sammel_zeile(daten, art, eps, ordnung, regel)
        f1s = [x[0] for x in w]
        assert median(f1s) == pytest.approx(alt["median"], abs=1e-6)
        assert sum(f1s) / len(f1s) == pytest.approx(alt["mittel"], abs=1e-6)
        assert sum(x < 0.8 for x in f1s) == alt["unter08"]
        assert sum(x[1] for x in w) / len(w) == pytest.approx(alt["sammel_mittel"], abs=1e-9)


def test_saetze_zur_gradfalle(daten):
    assert E.zaehle_gradfalle(daten) == (36, 13, 0) and "in **13** um mehr als 0,05 höher als nach p, in **0**" in README
    unterschiede = [E.sammel_zeile(daten, "nah", 1e-3, "p/Grad", r)["median"] - E.sammel_zeile(daten, "nah", 1e-3, "p", r)["median"] for r in M.SAMMEL_REGELN]
    assert max(unterschiede) == pytest.approx(0.008, abs=0.0005) and "höchstens 0,008" in README


@pytest.mark.parametrize("fall", ["hallen8", "a3_120"])
def test_regelmessung_neu_gerechnet(daten, fall):
    keys = M.regel_schluessel()
    ergebnisse = [laufe(g, ziel, s, keys) for g, ziel, s in M.regel_faelle(fall)]
    for k in keys:
        _gleich(kennzahlen([e[k] for e in ergebnisse]), daten["regel"][fall][f"{k[1][1]:g}|{k[2]}"])


def test_saetze_zur_regel(daten):
    r = daten["regel"]["hallen8"]
    assert round(r["0.0003|min"]["groesse"]) == 264 and round(r["0.0003|tal0.4"]["groesse"]) == 65
    e = E.nur_eps(daten, "a3_480")
    assert e["regel_spanne"] == pytest.approx(0, abs=1e-9)
    assert [E.de(m, 2) for m in e["mediane_min"]] == ["0,07", "0,16", "0,66"] and "von 0,07 über 0,16 auf 0,66" in README
    for eps in M.REGEL_EPS:                                             # auch bei Gruppen zu 120 ändert die Regel nichts
        werte = [daten["regel"]["a3_120"][f"{eps:g}|{regel}"]["median"] for regel in M.REGEL_REGELN]
        assert max(werte) - min(werte) < 1e-9


def test_fiedler_neu_gerechnet(daten):
    g = N.hallenverbund(M.VERBUND_TEST, 8)
    neu = fiedler_sweep(g, N.mittlere_halle(M.VERBUND_TEST, 8), 1)
    assert neu["f1"] < 0.01 and neu["abstand_ew"] == pytest.approx(daten["fiedler"]["hallen"][0]["abstand_ew"], rel=0.05)
    for i in (0, 2):
        g, ziel, _ = N.gemeinschaften(M.N_STANDARD, 60, 1.0, M.seed_von("fiedler", 1, 60, i))
        assert fiedler_sweep(g, ziel, 1)["f1"] == pytest.approx(daten["fiedler"]["gemein"][i][0]["f1"], abs=0.02)
    k = E.fiedler_kennzahlen(daten)
    assert (k["netze"], k["null"], k["treffer"], E.de(k["hoechstens"], 2)) == (20, 19, 0, "0,67")
    assert "2,5·10⁻⁶" in README and "in 19 Netzen unter 0,01, höchstens bei 0,67" in README


# ----------------------------------------------------------------------------------------------------------------------------------
# Zählungen und Fließtext
# ----------------------------------------------------------------------------------------------------------------------------------

def test_zaehlungen(daten):
    z = E.zaehlungen(daten)
    tal, kl = z["pagerank_tal"], z["pagerank_min"]
    assert (tal["zellen"], tal["sparsamer"], tal["median"], tal["treffer"], tal["vorn"], tal["zurueck"]) == (14, 14, 13, 9, 5, 5)
    assert tal["treffer_je_familie"] == {"a1": (5, 5), "a3": (4, 5), "hallen": (0, 4)}
    assert (kl["sparsamer"], kl["median"], kl["treffer"], kl["vorn"], kl["zurueck"]) == (14, 13, 11, 8, 1)
    assert kl["treffer_je_familie"] == {"a1": (5, 5), "a3": (4, 5), "hallen": (2, 4)}
    assert tal["gegner_treffer_vorn_je_familie"]["hallen"] == (4, 4)
    assert min(tal["faktor_min"], kl["faktor_min"]) > 5                       # „weniger als ein Fünftel“
    assert (E.de(tal["faktor_min"], 1), E.de(tal["faktor_max"], 0), E.de(kl["faktor_min"], 1), E.de(kl["faktor_max"], 0)) == ("6,5", "121", "5,6", "19")
    for zeile in ("| PageRank „erstes Tal“ | 14 von 14 | 6,5 bis 121 | 13 von 14 | 9 von 14 (Gemeinschaften 9 von 10, Hallen 0 von 4) | 5 / 5 |",
                  "| PageRank „min“ | 14 von 14 | 5,6 bis 19 | 13 von 14 | 11 von 14 (Gemeinschaften 9 von 10, Hallen 2 von 4) | 8 / 1 |"):
        assert zeile in README
    assert E.pagerank_nie_sparsamste(daten) == 0


def test_der_satz_ueber_das_sparsamste_verfahren_gilt_den_zwei_abgestimmten_pagerank_einstellungen(daten):
    """„Nie das sparsamste“ gilt den abgestimmten Einstellungen; die Push-Einstellung der Reihe gegen die Netzgröße („gleich viel“) ist keine davon."""
    vorfuehrung = ("pagerank", M.PUSH_VORFUEHRUNG, "min")
    for familie in M.FAMILIEN:
        for sweep in M.SWEEPS:
            assert M.schluessel_aus_wahl("pagerank", daten["wahl"][familie]["pagerank"][sweep]) != vorfuehrung, (familie, sweep)
        for zelle in M.innere_zellen(familie):
            t = daten["test"][familie][zelle]
            andere = min(t[v][s]["zugriffe"] for v in M.VERFAHREN_VERGLEICH if v != "pagerank" for s in M.SWEEPS)
            assert all(t["pagerank"][s]["zugriffe"] > andere for s in M.SWEEPS), (familie, zelle)
    for text in (README, E.sparsamste_und_lokal_text(daten)):
        assert "abgestimmten Einstellungen („erstes Tal“ und „min“)" in text and "ohne Blick auf die Treffer" in text
        assert "nicht über die feste Push-Einstellung" in text and "β = 0,006, ε = 0,0003, „min“" in text
        assert "liest auf wachsenden Netzen gleich viel, war aber" not in text


def test_waerme_und_lokalitaet(daten):
    w = E.waerme_vergleich(daten)
    assert w["summe"] == {"waerme": 590, "gierig": 585, "pagerank": 411} and w["laeufe"] == 600 and w["zellen"] == 10
    assert (w["waerme_mehr_als_gierig"], w["gierig_mehr_als_waerme"], w["waerme_mind_pagerank"], w["waerme_teuerste"]) == (4, 3, 8, 9)
    assert "Wärmeleitung 590, gierig 585, PageRank 411" in README
    lo, hi = E.lokalitaet(daten, "hallen", "pagerank", "tal", M.SEITEN_ABST)
    assert (E.de(lo, 1), E.de(hi, 1)) == ("2,9", "17,5") and "2,9- bis 17,5-Fache" in README
    lo, hi = E.lokalitaet(daten, "hallen", "pagerank", "tal")
    assert (E.de(lo, 1), E.de(hi, 1)) == ("1,8", "17,5") and "1,8- bis 17,5-fache" in README
    lo, hi = E.lokalitaet(daten, "hallen", "pagerank", "min")
    assert (E.de(lo, 2), E.de(hi, 2)) == ("0,25", "3,02") and "0,25- bis 3,02-Fache" in README
    lo, hi = E.lokalitaet(daten, "a3", "waerme", M.haupt_sweep(daten["wahl"]["a3"], "waerme"))
    assert (E.de(lo, 2), E.de(hi, 2)) == ("0,96", "1,33") and "0,96- bis 1,33-Fache" in README
    t = daten["test"]["hallen"]
    assert (t[6]["pagerank"]["min"]["treffer"], t[16]["pagerank"]["min"]["treffer"], t[20]["pagerank"]["min"]["treffer"]) == (23, 24, 0)


def test_ausserhalb_und_zweigipflig(daten):
    t = daten["test"]
    a1, a3 = t["a1"][960], t["a3"][960]
    assert (a1["gierig-nachbar"]["tal"]["treffer"], a1["pagerank"]["tal"]["treffer"], a1["waerme"]["tal"]["treffer"]) == (0, 36, 48)
    assert (a3["gierig-nachbar"]["tal"]["treffer"], a3["pagerank"]["tal"]["treffer"], a3["waerme"]["tal"]["treffer"]) == (0, 0, 39)
    assert (t["a3"][20]["gierig-nachbar"]["tal"]["treffer"], t["a3"][20]["pagerank"]["tal"]["treffer"]) == (24, 46)
    zellen = [t[f][z]["gierig-entdeckt"][M.haupt_sweep(daten["wahl"][f], "gierig-entdeckt")] for f in ("a1", "a3") for z in M.GROESSEN_ABST]
    unter = [60 - w["treffer"] for w in zellen]
    assert (min(unter), max(unter)) == (2, 28) and min(w["median"] for w in zellen) >= 0.905
    assert "2 bis 28 von 60" in README and "mindestens 0,91" in README
    # beste gierige Fassung je Familie, wie in der README genannt
    assert [M.beste_gierige(daten["wahl"][f])[0] for f in M.FAMILIEN] == ["gierig-nachbar", "gierig-nachbar", "gierig-entdeckt"]


def test_ergebnisdatei_vollstaendig(daten):
    for f in M.FAMILIEN:
        assert set(daten["test"][f]) == set(M.test_zellen(f))
        for z in M.test_zellen(f):
            assert daten["test"][f][z]["pagerank"]["tal"]["zahl"] == len(list(M.test_nummern(f, z)))


def test_keine_planbegriffe_oder_verbotenen_woerter_in_app_und_readme():
    texte = README + (ROOT / "app.py").read_text(encoding="utf-8") + (ROOT / "lsn_evaluation.py").read_text(encoding="utf-8") + (
        ROOT / "lsn_constants.py").read_text(encoding="utf-8")
    for muster in (r"\bStück\s*\d", r"Phase 0", r"Pilot", r"Korrekturrunde", r"Saatwert", r"\bträgt\b", r"läuft lokal", r"\bVorformung\b"):
        assert not re.search(muster, texte), muster
