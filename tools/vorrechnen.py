"""Rechnet `daten/vorgerechnet.json` (Abstimmung, Test und Zusatzmessungen) aus den Definitionen in `lsn_messen.py`.

Aufruf (aus dem Demo-Ordner, in Etappen; jede Etappe bricht nach `--grenze` Sekunden ab und setzt beim nächsten Aufruf fort):

    python tools/vorrechnen.py --ablage <Ordner> abst <a1|a3|hallen> <gierig|pagerank|waerme>
    python tools/vorrechnen.py --ablage <Ordner> wahl
    python tools/vorrechnen.py --ablage <Ordner> test <a1|a3|hallen>
    python tools/vorrechnen.py --ablage <Ordner> zusatz <sammel|n|verbund|regel|anteil|fiedler|kanten>
    python tools/vorrechnen.py --ablage <Ordner> bericht

Zwischenstände (Pickle) liegen nur im Ablage-Ordner. `bericht` schreibt die JSON-Datei."""

import argparse
import json
import os
import pickle
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import numpy as np  # noqa: E402

import lsn_messen as M  # noqa: E402
import lsn_netze as N  # noqa: E402
import lsn_sweep as W  # noqa: E402
from lsn_diffusion import ppr_exakt, push  # noqa: E402
from lsn_fiedler import fiedler_sweep  # noqa: E402
from lsn_verfahren import Ergebnis, kennzahlen, laufe, median  # noqa: E402

ZIEL = ROOT / "daten" / "vorgerechnet.json"


class Ablage:
    def __init__(self, ordner: str, name: str):
        self.pfad = Path(ordner) / f"{name}.pkl"
        self.daten = pickle.loads(self.pfad.read_bytes()) if self.pfad.exists() else {}

    def speichern(self):
        tmp = self.pfad.with_suffix(".tmp")
        tmp.write_bytes(pickle.dumps(self.daten))
        os.replace(tmp, self.pfad)


def etappe(ablage: Ablage, faelle, rechne, grenze: float):
    """Rechnet die noch fehlenden Fälle, bis die Zeitgrenze erreicht ist."""
    t0 = letzte = time.time()
    offen = fertig = 0
    for schluessel, fall in faelle:
        if schluessel in ablage.daten:
            continue
        if time.time() - t0 > grenze:
            offen += 1
            continue
        ablage.daten[schluessel] = rechne(fall)
        fertig += 1
        if time.time() - letzte > 30:
            ablage.speichern()
            letzte = time.time()
    ablage.speichern()
    print(f"{ablage.pfad.stem}: neu {fertig}, gesamt {len(ablage.daten)}, offen {offen}, {time.time() - t0:.0f} s", flush=True)


def cmd_abst(args):
    keys = M.raster(args.gruppe)
    faelle = (((z, i), bau) for z, i, bau in M.abstimm_faelle(args.familie))
    etappe(Ablage(args.ablage, f"abst_{args.familie}_{args.gruppe}"), faelle, lambda bau: laufe(*bau(), keys), args.grenze)


def lade_abstimmung(ordner: str, familie: str) -> dict:
    gesamt = {}
    for gruppe in M.GRUPPEN:
        daten = Ablage(ordner, f"abst_{familie}_{gruppe}").daten
        erwartet = len(list(M.abstimm_faelle(familie)))
        if len(daten) != erwartet:
            raise SystemExit(f"abst {familie} {gruppe}: {len(daten)} von {erwartet} Fällen")
        for name, werte in daten.items():
            gesamt.setdefault(name, {}).update(werte)
    return gesamt


def cmd_wahl(args):
    wahl = {f: M.waehle_einstellungen(lade_abstimmung(args.ablage, f), M.innere_zellen(f)) for f in M.FAMILIEN}
    (Path(args.ablage) / "wahl.pkl").write_bytes(pickle.dumps(wahl))
    for f in M.FAMILIEN:
        for v, zeilen in wahl[f].items():
            for s, w in zeilen.items():
                print(f"WAHL {f} {v:16s} {s}: par={w['par']} {w['regel']:8s} Abst {w['abst_mittel']:.4f} (Höchstwert {w['abst_hoechstwert']:.4f}) "
                      f"Zugriffe {w['abst_zugriffe']:.0f} Rand {'+'.join(w['rand']) or '-'}")
        print(f"  beste gierige: {M.beste_gierige(wahl[f])}; Haupt-Sweep pagerank {M.haupt_sweep(wahl[f], 'pagerank')}, waerme {M.haupt_sweep(wahl[f], 'waerme')}")


def lade_wahl(ordner: str) -> dict:
    return pickle.loads((Path(ordner) / "wahl.pkl").read_bytes())


def cmd_test(args):
    keys = M.test_schluessel(lade_wahl(args.ablage)[args.familie])
    faelle = (((z, i), bau) for z, i, bau in M.test_faelle(args.familie))
    etappe(Ablage(args.ablage, f"test_{args.familie}"), faelle, lambda bau: laufe(*bau(), keys), args.grenze)


def rechne_sammel(fall):
    art, i = fall
    g, ziel, s, sammel = M.sammel_fall(art, i)
    erg = {}
    for eps in M.SAMMEL_EPS:
        p, _, _, _ = push(g, s, M.SAMMEL_BETA, eps)
        for ordnung in M.ORDNUNGEN:
            reihe = W.reihe_nach(g, p, normiert=ordnung == "p/Grad") or [s]
            phis, _ = W.kurve(g, reihe)
            treffer = W.kumulierte_treffer(reihe, ziel)
            for regel in M.SAMMEL_REGELN:
                k = W.waehle(phis, regel)
                erg[(eps, ordnung, regel)] = (W.f1(treffer[k], k, len(ziel)), len(sammel & set(reihe[:k])), k)
    return erg


def cmd_zusatz(args):
    wahl_pfad = Path(args.ablage) / "wahl.pkl"
    if args.teil == "sammel":
        faelle = (((art, i), (art, i)) for art in M.SAMMEL_ARTEN for i in range(M.SAMMEL_NETZE))
        etappe(Ablage(args.ablage, "z_sammel"), faelle, rechne_sammel, args.grenze)
    elif args.teil == "n":
        schluessel = M.n_reihe_schluessel(pickle.loads(wahl_pfad.read_bytes())["a1"])

        def rechne(fall):
            g, ziel, s = M.n_reihe_fall(*fall)
            erg = laufe(g, ziel, s, list(schluessel.values()))
            p, r, _, _ = push(g, s, *M.PUSH_VORFUEHRUNG)
            return {"erg": {name: tuple(erg[k]) for name, k in schluessel.items()}, "vol": g.vol, "n": g.n, "beruehrt": len(r.keys() | p.keys()) / g.n}

        faelle = (((n, i), (n, i)) for n in M.N_REIHE for i in range(M.N_REIHE_NETZE))
        etappe(Ablage(args.ablage, "z_n"), faelle, rechne, args.grenze)
    elif args.teil == "verbund":
        def rechne(z):
            faelle_z = list(M.verbund_reihe_faelle(z))
            erg = [tuple(laufe(g, ziel, s, [M.VERBUND_REIHE_SCHLUESSEL])[M.VERBUND_REIHE_SCHLUESSEL]) for g, ziel, s in faelle_z]
            return {"erg": erg, "n": faelle_z[0][0].n, "vol": faelle_z[0][0].vol}

        etappe(Ablage(args.ablage, "z_verbund"), ((z, z) for z in M.VERBUND_REIHE_Z), rechne, args.grenze)
    elif args.teil == "regel":
        keys = M.regel_schluessel()

        def rechne(name):
            return [laufe(g, ziel, s, keys) for g, ziel, s in M.regel_faelle(name)]

        etappe(Ablage(args.ablage, "z_regel"), ((n, n) for n in M.REGEL_FAELLE), rechne, args.grenze)
    elif args.teil == "anteil":
        z, a = M.ANTEIL_Z, M.ANTEIL_A
        g = N.hallenverbund(z, a)
        ziel = sorted(N.mittlere_halle(z, a))

        def rechne(beta):
            return [float(ppr_exakt(g, s, beta)[ziel].sum()) for s in ziel]

        etappe(Ablage(args.ablage, "z_anteil"), ((b, b) for b in M.ANTEIL_BETAS), rechne, args.grenze)
    elif args.teil == "fiedler":
        def rechne(fall):
            if fall == "hallen":
                g = N.hallenverbund(M.VERBUND_TEST, 8)
                ziel = N.mittlere_halle(M.VERBUND_TEST, 8)
            else:
                g, ziel, _ = N.gemeinschaften(M.N_STANDARD, 60, 1.0, M.seed_von("fiedler", 1, 60, fall))
            return [fiedler_sweep(g, ziel, startwert) for startwert in (1, 2)]

        etappe(Ablage(args.ablage, "z_fiedler"), ((f, f) for f in ("hallen", *range(M.FIEDLER_NETZE))), rechne, args.grenze)
    elif args.teil == "kanten":
        def rechne(familie):
            erg = {}
            for zelle in M.test_zellen(familie):
                nummern = list(M.test_nummern(familie, zelle))
                if familie == "hallen":
                    erg[zelle] = (M.test_fall(familie, zelle, 0)[0].vol, M.test_fall(familie, zelle, 0)[0].n)
                else:
                    netze = [M.test_fall(familie, zelle, i)[0] for i in nummern]
                    erg[zelle] = (median([g.vol for g in netze]), median([g.n for g in netze]))
            return erg

        etappe(Ablage(args.ablage, "z_kanten"), ((f, f) for f in M.FAMILIEN), rechne, args.grenze)


def cmd_bericht(args):
    wahl = lade_wahl(args.ablage)
    daten = {"wahl": wahl, "test": {}, "netze": {}}
    for f in M.FAMILIEN:
        roh = Ablage(args.ablage, f"test_{f}").daten
        erwartet = len(list(M.test_faelle(f)))
        if len(roh) != erwartet:
            raise SystemExit(f"test {f}: {len(roh)} von {erwartet} Fällen")
        daten["test"][f] = M.zellen_kennzahlen(roh, wahl[f], M.test_zellen(f))
    kanten = Ablage(args.ablage, "z_kanten").daten
    daten["netze"] = {f: {z: {"vol": v, "n": n} for z, (v, n) in kanten[f].items()} for f in M.FAMILIEN}

    sammel = Ablage(args.ablage, "z_sammel").daten
    daten["sammel"] = {}
    for art in M.SAMMEL_ARTEN:
        faelle = [sammel[(art, i)] for i in range(M.SAMMEL_NETZE)]
        eintrag = {}
        for eps in M.SAMMEL_EPS:
            for ordnung in M.ORDNUNGEN:
                for regel in M.SAMMEL_REGELN:
                    werte = [f[(eps, ordnung, regel)] for f in faelle]
                    f1s = [w[0] for w in werte]
                    eintrag[f"{eps:g}|{ordnung}|{regel}"] = {
                        "f1": [round(x, 4) for x in f1s], "median": median(f1s), "mittel": sum(f1s) / len(f1s), "unter08": sum(x < 0.8 for x in f1s),
                        "treffer": sum(x >= 0.9 - 1e-12 for x in f1s), "sammel_mittel": sum(w[1] for w in werte) / len(werte), "groesse": median([w[2] for w in werte])}
        daten["sammel"][art] = eintrag

    nroh = Ablage(args.ablage, "z_n").daten
    daten["n_reihe"] = {}
    for n in M.N_REIHE:
        faelle = [nroh[(n, i)] for i in range(M.N_REIHE_NETZE)]
        daten["n_reihe"][n] = {"vol": median([f["vol"] for f in faelle]), "n": median([f["n"] for f in faelle]), "beruehrt": median([f["beruehrt"] for f in faelle]),
                               "kurven": {name: kennzahlen([Ergebnis(*f["erg"][name]) for f in faelle]) for name in faelle[0]["erg"]}}

    verbund = Ablage(args.ablage, "z_verbund").daten
    daten["verbund_reihe"] = {z: {"n": verbund[z]["n"], "vol": verbund[z]["vol"], **kennzahlen([Ergebnis(*e) for e in verbund[z]["erg"]])} for z in M.VERBUND_REIHE_Z}

    regel = Ablage(args.ablage, "z_regel").daten
    daten["regel"] = {name: {f"{k[1][1]:g}|{k[2]}": kennzahlen([lauf[k] for lauf in regel[name]]) for k in M.regel_schluessel()} for name in M.REGEL_FAELLE}

    anteil = Ablage(args.ablage, "z_anteil").daten
    reihen = [anteil[b] for b in M.ANTEIL_BETAS]
    monoton = sum(all(reihen[j][i] > reihen[j + 1][i] for j in range(len(reihen) - 1)) for i in range(len(reihen[0])))
    daten["anteil"] = {"betas": list(M.ANTEIL_BETAS), "median": [median(r) for r in reihen], "minimum": [min(r) for r in reihen], "maximum": [max(r) for r in reihen],
                       "starts": len(reihen[0]), "monoton": monoton}

    fiedler = Ablage(args.ablage, "z_fiedler").daten
    daten["fiedler"] = {"hallen": fiedler["hallen"], "gemein": [fiedler[i] for i in range(M.FIEDLER_NETZE)]}

    ZIEL.parent.mkdir(exist_ok=True)
    ZIEL.write_text(json.dumps(daten, ensure_ascii=False, indent=1, default=_json), encoding="utf-8", newline="\n")
    print(f"geschrieben: {ZIEL} ({ZIEL.stat().st_size // 1024} KB)")


def _json(x):
    if isinstance(x, np.generic):
        return x.item()
    raise TypeError(type(x))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--ablage", required=True, help="Ordner für Zwischenstände")
    ap.add_argument("--grenze", type=float, default=400.0, help="Sekunden je Etappe")
    sub = ap.add_subparsers(dest="befehl", required=True)
    p = sub.add_parser("abst")
    p.add_argument("familie", choices=M.FAMILIEN)
    p.add_argument("gruppe", choices=list(M.GRUPPEN))
    sub.add_parser("wahl")
    p = sub.add_parser("test")
    p.add_argument("familie", choices=M.FAMILIEN)
    p = sub.add_parser("zusatz")
    p.add_argument("teil", choices=("sammel", "n", "verbund", "regel", "anteil", "fiedler", "kanten"))
    sub.add_parser("bericht")
    args = ap.parse_args()
    Path(args.ablage).mkdir(parents=True, exist_ok=True)
    {"abst": cmd_abst, "wahl": cmd_wahl, "test": cmd_test, "zusatz": cmd_zusatz, "bericht": cmd_bericht}[args.befehl](args)


if __name__ == "__main__":
    main()
