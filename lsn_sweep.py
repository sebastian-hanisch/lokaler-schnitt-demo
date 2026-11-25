"""Sweep, Konduktanz und Treffergüte. Ohne Streamlit.

**Konduktanz** (conductance) einer Menge S: Randkanten / min(Volumen S, Volumen Rest); Volumen = Summe der Grade. **Sweep:** Plätze nach p/Grad ordnen und ein
Anfangsstück wählen. Regel `min`: das Anfangsstück mit der kleinsten Konduktanz. Regel `talγ` („erstes Tal“ mit Schwelle γ): das erste laufende Minimum ab
5 Plätzen, nach dem die Konduktanz um den Faktor 1 + γ steigt; gibt es keines, gilt `min`. Gleichstände: das erste Minimum (Toleranz 10⁻¹²), in der Ordnung die
kleinere Nummer. **F1** gegen die gepflanzte Menge C: 2·|S ∩ C| / (|S| + |C|). **Treffer:** F1 ≥ 0,9."""

from fractions import Fraction

MINDEST = 5
TREFFER_AB = 0.9


def regel_gamma(regel: str):
    """None bei `min`, sonst die Schwelle γ aus `talγ`."""
    if regel == "min":
        return None
    if not regel.startswith("tal"):
        raise ValueError(f"unbekannte Sweep-Regel {regel}")
    return float(regel[3:])


def regel_name(gamma) -> str:
    return "min" if gamma is None else f"tal{gamma:g}"


def reihe_nach(g, werte: dict, normiert: bool = True) -> list:
    """Plätze mit positivem Wert, absteigend nach Wert/Grad (oder nach dem Wert allein), bei Gleichstand nach Nummer."""
    if normiert:
        return sorted((u for u in werte if werte[u] > 0), key=lambda u: (-werte[u] / max(g.d[u], 1), u))
    return sorted((u for u in werte if werte[u] > 0), key=lambda u: (-werte[u], u))


def kurve(g, reihe: list):
    """Konduktanz und Volumen jedes Anfangsstücks (fortlaufend gezählt). Ein Anfangsstück ohne Gegenüber (Nenner 0) bekommt 2, damit es nie gewählt wird."""
    drin = set()
    vol = rand = 0
    phis, vols = [], []
    nb, d, gesamt = g.nb, g.d, g.vol
    for u in reihe:
        innen = 0
        for v in nb[u]:
            if v in drin:
                innen += 1
        drin.add(u)
        vol += d[u]
        rand += d[u] - 2 * innen
        nenner = vol if vol <= gesamt - vol else gesamt - vol
        phis.append(rand / nenner if nenner > 0 else 2.0)
        vols.append(vol)
    return phis, vols


def waehle(phis: list, regel: str, laenge: int = None) -> int:
    """Länge des gewählten Anfangsstücks unter den ersten `laenge` Plätzen."""
    laenge = len(phis) if laenge is None else laenge
    gamma = regel_gamma(regel)
    if gamma is not None:
        best, bk = 2.0, 0
        for k in range(1, laenge + 1):
            f = phis[k - 1]
            if k >= MINDEST and f < best - 1e-12:
                best, bk = f, k
            elif bk and f > best * (1 + gamma):
                return bk
    best, bk = 2.0, 0
    for k in range(1, laenge + 1):
        if phis[k - 1] < best - 1e-12:
            best, bk = phis[k - 1], k
    return bk if bk else min(1, laenge)           # nur Nenner 0: dann bleibt der erste Platz


def kumulierte_treffer(reihe: list, ziel) -> list:
    """Zahl der Plätze aus `ziel` je Anfangsstück (Index = Länge)."""
    t, erg = 0, [0]
    for u in reihe:
        t += u in ziel
        erg.append(t)
    return erg


def f1(schnittmenge: int, groesse: int, ziel_groesse: int) -> float:
    return 2 * schnittmenge / (groesse + ziel_groesse) if groesse + ziel_groesse else 0.0


def f1_menge(menge, ziel) -> float:
    return f1(len(set(menge) & set(ziel)), len(set(menge)), len(ziel))


def rand_und_volumen(g, menge):
    s = set(menge)
    vol = sum(g.d[u] for u in s)
    rand = sum(1 for u in s for v in g.nb[u] if v not in s)
    return rand, vol


def konduktanz(g, menge) -> Fraction:
    """Exakt als Bruch; für die leere Menge oder das ganze Netz nicht definiert."""
    rand, vol = rand_und_volumen(g, menge)
    nenner = min(vol, g.vol - vol)
    if nenner <= 0:
        raise ValueError("Konduktanz nur für Mengen mit Volumen auf beiden Seiten")
    return Fraction(rand, nenner)
