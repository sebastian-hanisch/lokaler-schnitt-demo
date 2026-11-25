"""Globaler Fiedler-Sweep als Bezug: er sucht die beste Zweiteilung des ganzen Netzes, nicht die Gemeinschaft eines Startplatzes. Ohne Streamlit.

Berechnet werden die drei größten Eigenwerte von I + N mit N = D^(−1/2)·A·D^(−1/2) (der größte ist 2); der Eigenvektor zum zweitgrößten, geteilt durch √Grad, ordnet
die Plätze. Von beiden Enden dieser Ordnung wird das Anfangsstück mit der kleinsten Konduktanz gesucht und bei mehr als halbem Volumen durch sein Gegenstück ersetzt.
Liegen der zweite und der dritte Eigenwert sehr nahe beieinander, ist der Vektor schlecht bestimmt und die Menge hängt vom Lösungsweg ab."""

import numpy as np
from scipy.sparse import diags, identity
from scipy.sparse.linalg import eigsh

import lsn_sweep as W
from lsn_diffusion import adjazenz_matrix


def fiedler_sweep(g, ziel, startwert: int = 1) -> dict:
    """Gibt die bessere der beiden Seiten (kleinere Konduktanz) mit Größe, F1 gegen `ziel`, Konduktanz und dem Abstand zwischen zweitem und drittem Eigenwert."""
    d = np.maximum(np.array(g.d, dtype=float), 1.0)
    w = 1.0 / np.sqrt(d)
    M = (diags(w) @ adjazenz_matrix(g) @ diags(w) + identity(g.n)).tocsc()
    v0 = np.random.default_rng(startwert).random(g.n)
    werte, V = eigsh(M, k=3, which="LA", tol=1e-9, v0=v0, ncv=60, maxiter=200000)
    ordnung = np.argsort(werte)[::-1]
    y = V[:, ordnung[1]] * w
    beste = None
    for vorzeichen in (1, -1):
        reihe = [int(i) for i in np.argsort(vorzeichen * y, kind="stable")]
        phis, vols = W.kurve(g, reihe)
        k = W.waehle(phis[:-1], "min")
        menge = set(reihe[:k])
        if vols[k - 1] > g.vol / 2:
            menge = set(range(g.n)) - menge
        kandidat = {"konduktanz": phis[k - 1], "groesse": len(menge), "f1": W.f1_menge(menge, ziel),
                    "abstand_ew": float(werte[ordnung[1]] - werte[ordnung[2]])}
        if beste is None or kandidat["konduktanz"] < beste["konduktanz"]:
            beste = kandidat
    return beste
