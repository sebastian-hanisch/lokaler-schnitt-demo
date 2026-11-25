"""Die zwei Ausbreitungsverfahren: Push für das personalisierte PageRank (Irrfahrt mit Neustart) und eine abgeschnittene Wärmeleitung. Ohne Streamlit.

**Irrfahrt mit zufälligem Neustart:** In jedem Schritt springt sie mit der Sprungwahrscheinlichkeit β zum Start zurück, sonst geht sie zu einem zufälligen Nachbarn
(nicht träge). Ihre langfristige Verteilung ist p = β·e_s + (1 − β)·p·P.

**Push** (Reihenfolge Warteschlange, Anfang der Start; die Reihenfolge ist Teil der Definition): Jeder Platz u hat einen Wert p(u) und einen Rest r(u). Solange
r(u) ≥ ε·Grad(u), gilt: p(u) += β·r(u), der Rest (1 − β)·r(u) geht zu gleichen Teilen an die Nachbarn, r(u) = 0. Zähleinheit Kantenzugriffe: Summe der Grade aller
bearbeiteten Plätze, Wiederholungen mitgezählt. Die **träge** Fassung (Andersen, Chung und Lang, nur für den Vergleich) behält die Hälfte des Rests am Platz und rechnet
mit α = β/(2 − β); sie hat dieselbe Zielgröße.

**Wärmeleitung** (eigene abgeschnittene Fassung, nicht das Verfahren von Kloster und Gleich): h = Σ_k e^(−t)·t^k/k!·(Start·P^k), die Reihe bis zu einem Rest von höchstens
10⁻³; vor jedem Schritt werden Einträge unter δ·Grad nicht weitergegeben."""

from collections import deque

import numpy as np
from scipy.sparse import csr_matrix, diags
from scipy.sparse.linalg import cg

from lsn_zufall import exact_exp

WAERME_REST = 1e-3


def push(g, s: int, beta: float, eps: float, traege: bool = False, protokoll: list = None, protokoll_grenze: int = None):
    """Gibt (p, r, Kantenzugriffe, Zahl der Pushes). p und r sind Wörterbücher über die berührten Plätze.

    protokoll: wird eine Liste übergeben, bekommt sie je Push (Platz, geschobener Rest, p-Kopie, r-Kopie), höchstens `protokoll_grenze` Einträge, für die
    Schritt-für-Schritt-Ansicht kleiner Netze."""
    if not 0 < beta < 1 or eps <= 0:
        raise ValueError("0 < β < 1 und ε > 0")
    nb, d = g.nb, g.d
    n = len(nb)
    p, r = [0.0] * n, [0.0] * n
    beruehrt = [s]
    gesehen = bytearray(n)
    gesehen[s] = 1
    r[s] = 1.0
    schlange = deque((s,))
    wartet = bytearray(n)
    wartet[s] = 1
    zugriffe = pushes = 0
    alpha = beta / (2 - beta)
    while schlange:
        u = schlange.popleft()
        wartet[u] = 0
        du = d[u]
        ru = r[u]
        if du == 0 or ru < eps * du:
            continue
        if traege:
            p[u] += alpha * ru
            r[u] = (1 - alpha) * ru / 2
            teil = (1 - alpha) * ru / (2 * du)
        else:
            p[u] += beta * ru
            r[u] = 0.0
            teil = (1 - beta) * ru / du
        zugriffe += du
        pushes += 1
        for v in nb[u]:
            x = r[v] + teil
            r[v] = x
            if not gesehen[v]:
                gesehen[v] = 1
                beruehrt.append(v)
            if x >= eps * d[v] and not wartet[v]:
                schlange.append(v)
                wartet[v] = 1
        if traege and r[u] >= eps * du and not wartet[u]:
            schlange.append(u)
            wartet[u] = 1
        if protokoll is not None and (protokoll_grenze is None or len(protokoll) < protokoll_grenze):
            protokoll.append((u, ru, {i: p[i] for i in beruehrt if p[i]}, {i: r[i] for i in beruehrt if r[i]}))
    return {i: p[i] for i in beruehrt if p[i] > 0}, {i: r[i] for i in beruehrt if r[i] > 0}, zugriffe, pushes


def adjazenz_matrix(g) -> csr_matrix:
    zeilen = np.repeat(np.arange(g.n), g.d)
    spalten = np.fromiter((v for x in g.nb for v in x), dtype=np.int64, count=g.vol)
    return csr_matrix((np.ones(len(zeilen)), (zeilen, spalten)), shape=(g.n, g.n))


def ppr_exakt(g, s: int, beta: float, toleranz: float = 1e-12) -> np.ndarray:
    """Das personalisierte PageRank ab s aus dem Gleichungssystem (D − (1−β)A)·y = β·e_s mit p = D·y (y ist p/Grad).

    Die Matrix ist symmetrisch und positiv definit; gelöst wird mit konjugierten Gradienten und Diagonal-Vorbereitung, ohne Zufall. Plätze ohne Nachbarn
    bekommen den Wert 0 (außer s selbst, der dann alles behält)."""
    d = np.array(g.d, dtype=float)
    if g.d[s] == 0:
        p = np.zeros(g.n)
        p[s] = 1.0
        return p
    diagonale = np.where(d > 0, d, 1.0)
    M = (diags(diagonale) - (1 - beta) * adjazenz_matrix(g)).tocsr()
    b = np.zeros(g.n)
    b[s] = beta
    y, info = cg(M, b, rtol=toleranz, atol=0.0, maxiter=20000, M=diags(1.0 / diagonale))
    if info != 0:
        raise RuntimeError("konjugierte Gradienten nicht konvergiert")
    return diagonale * y


def waerme_gewichte(t: float):
    """Reihengewichte e^(−t)·t^k/k! für k = 0 … K, K kleinstes mit Rest höchstens 10⁻³."""
    gewicht = exact_exp(-t)
    gewichte, summe = [gewicht], gewicht
    while 1 - summe > WAERME_REST:
        gewicht *= t / len(gewichte)
        gewichte.append(gewicht)
        summe += gewicht
    return gewichte


def waerme(g, s: int, t: float, delta: float):
    """Abgeschnittene Wärmeleitung. Gibt (h als Wörterbuch, Kantenzugriffe)."""
    nb, d = g.nb, g.d
    gewichte = waerme_gewichte(t)
    h, x = {}, {s: 1.0}
    zugriffe = 0
    for k, gewicht in enumerate(gewichte):
        for u, w in x.items():
            h[u] = h.get(u, 0.0) + gewicht * w
        if k == len(gewichte) - 1:
            break
        neu = {}
        for u, w in x.items():
            du = d[u]
            if du == 0 or w < delta * du:
                continue
            zugriffe += du
            teil = w / du
            for v in nb[u]:
                neu[v] = neu.get(v, 0.0) + teil
        x = neu
        if not x:
            break
    return h, zugriffe
