"""Irrfahrt mit Neustart: der lokale Schnitt - interaktive Konzept-Demo
Sebastian Hanisch - Operations Research und Machine Learning

Eine Irrfahrt mit zufälligem Neustart (personalisiertes PageRank, hier mit dem Push-Verfahren) gewichtet die Plätze um einen Start, ein Sweep schneidet daraus eine
Menge. Fünf Experimente: der Neustart, die Division durch den Grad, der Aufwand gegen die Netzgröße, die gefundene Größe und die Gegner (gierige Erweiterung,
Wärmeleitung, Breitensuche). Aufbau und Regeln stehen im DEMO-PLAYBOOK.md (§2).

Lauffähig mit: streamlit run app.py
"""

import pandas as pd
import streamlit as st

import lsn_constants as C
import lsn_daten as D
import lsn_evaluation as E
import lsn_messen as M
import lsn_scenario as S
import lsn_visualization as V
from lsn_layout import dunkles_design, kopf_css
from lsn_presets import (
    bounds,
    init_session_state_defaults,
    load_permalink_settings,
    randomize_seed,
    sidebar_presets,
    sync_query_params,
)
from lsn_verfahren import reihe_und_zugriffe, schnitt, schnitt_aus
from lsn_wachsen import GIERIG

st.set_page_config(page_title="Lokaler Schnitt – Sebastian Hanisch", layout="wide")

URL = "https://sebastianhanisch-{}.streamlit.app/"
SCHLUESSEL = ("netz", "a", "z", "groesse", "aussen", "n", "sammelart", "start_platz", "start_halle", "verfahren", "beta", "eps", "regel", "gamma", "gierig_art",
              "budget", "seed")


@st.cache_resource(show_spinner=False, max_entries=6)
def _szenario(netz, a, z, groesse, aussen, n, sammelart, start_platz, start_halle, seed):
    return S.baue(netz, a, z, groesse, aussen, n, sammelart, start_platz, start_halle, seed)


@st.cache_data(show_spinner=False)
def _daten():
    return D.laden()


@st.cache_data(show_spinner=False, max_entries=6)
def _ausbreitung(szenario_schluessel, verfahren, par):
    """Push bzw. Wärmeleitung bzw. Breitensuche einmal rechnen; die Sweep-Regeln teilen sich das Ergebnis."""
    sz_ = _szenario(*szenario_schluessel)
    return reihe_und_zugriffe(sz_.g, sz_.start, verfahren, par)


@st.cache_data(show_spinner=False, max_entries=24)
def _schnitt(szenario_schluessel, verfahren, par, regel, normiert=True):
    sz_ = _szenario(*szenario_schluessel)
    if verfahren in GIERIG:
        return schnitt(sz_.g, sz_.ziel, sz_.start, verfahren, par, regel)
    return schnitt_aus(sz_.g, sz_.ziel, sz_.start, _ausbreitung(szenario_schluessel, verfahren, par), regel, normiert)


@st.cache_data(show_spinner=False, max_entries=20)
def _neustart(szenario_schluessel, beta):
    n = E.neustart(_szenario(*szenario_schluessel), beta)
    return n.p, n.anteil_ziel, n.betas, n.anteile


@st.cache_data(show_spinner=False, max_entries=20)
def _protokoll(szenario_schluessel, beta, eps):
    return E.push_protokoll(_szenario(*szenario_schluessel), beta, eps)


@st.cache_data(show_spinner=False, max_entries=20)
def _push_zaehlung(szenario_schluessel, beta, eps):
    return E.push_zaehlung(_szenario(*szenario_schluessel), beta, eps)


@st.cache_data(show_spinner=False, max_entries=10)
def _live(szenario_schluessel):
    return E.live_vergleich(_szenario(*szenario_schluessel), _daten()["wahl"])


# Fester Kopf: nur der Titel bleibt beim Scrollen oben (Stylesheet in lsn_layout.py).
st.html(kopf_css(dunkles_design()))
st.html('<style>[data-testid="stMarkdownContainer"] table { display: block; overflow-x: auto; max-width: 100%; }</style>')   # breite Tabellen scrollen auf dem Telefon
with st.container(key="kopf"):
    st.title("✂️ Irrfahrt mit Neustart: der lokale Schnitt")
st.markdown(
    """
**Mit Neustart liest man gleich viel. Aber welche Menge herauskommt, entscheidet nicht der PageRank allein.** Eine **Irrfahrt mit Neustart** (personalisiertes PageRank)
misst Nähe zu einem Startplatz; mit dem **Push-Verfahren** und einem **Sweep** schneidet man daraus eine Menge um den Start. „Gleich viel“ gilt hier für **wachsende
Zufallsgemeinschaften** bei fester Einstellung: Auf großen Netzen liest der Push nur einen kleinen Teil, auf kleinen oder mit sehr kleinem ε mehr, als das ganze Netz
Verbindungen hat. Welche Menge herauskommt, hängt auch an der **Division durch den Grad**, der **Regel am Sweep** und den **Parametern**.

Weiter unten: **❓ Kernfragen**, fünf **🔬 Experimente**, **🚧 Wo die Annahmen enden** und die Expander **⚠️ Annahmen, Grenzen und bekannte Probleme** und
**📐 Mathematische Formulierung**.
"""
)

with st.expander("So funktioniert der lokale Schnitt", expanded=True):
    st.markdown(
        f"""
1. **Neustart.** In jedem Schritt springt die Irrfahrt mit der **Sprungwahrscheinlichkeit β** zum Start zurück, sonst geht sie zu einem zufälligen Nachbarn (sie
   bleibt nie stehen). Auf lange Sicht ist sie dann bei Plätzen nahe am Start häufiger; diese Verteilung heißt **personalisiertes PageRank** p.
2. **Push** (Verfahren nach Andersen, Chung und Lang, hier in der nicht trägen Fassung). Statt die Irrfahrt zu simulieren, schiebt man Wahrscheinlichkeit weiter: jeder
   Platz hat einen Wert p und einen Rest r. Ist r mindestens ε mal die Nachbarzahl, bekommt p den Anteil β des Rests, der übrige Rest geht gleich an die Nachbarn.
   Gezählt werden **Kantenzugriffe**: die Nachbarzahlen aller bearbeiteten Plätze, Wiederholungen mitgezählt. Sie sind höchstens 1/(β·ε).
3. **Sweep.** Die Plätze werden nach **p geteilt durch die Nachbarzahl** (Grad) geordnet. Von den Anfangsstücken dieser Ordnung wählt eine Regel eines: **min** nimmt
   die kleinste **Konduktanz** (conductance: Randverbindungen geteilt durch das kleinere Volumen, Volumen = Summe der Grade), **erstes Tal** hält beim ersten Tal an,
   nach dem die Konduktanz wieder um den Anteil γ steigt.
4. **Gegner.** Eine **gierige Erweiterung** nimmt immer den Randplatz mit dem größten Anteil seiner Verbindungen in die Menge auf, bis ein Volumenbudget B erreicht ist;
   dazu eine **Wärmeleitungs-Diffusion** (heat kernel; eigene abgeschnittene Fassung) und eine **Breitensuche-Kugel**.
5. **Netze.** Zwei Handnetze zum Nachrechnen; ein **Hallenverbund** (Gitterhallen, benachbarte Hallen durch je eine Tür verbunden; die Hallen sind eine Kulisse) und
   **Zufallsgemeinschaften** (Gruppen, in denen jeder Platz im Mittel 8 Nachbarn hat, dazu wenige Verbindungen nach außen), auf Wunsch mit **Sammelpunkten** (Plätze mit
   sehr vielen Verbindungen). In jedem Netz ist eine Menge **gepflanzt**: die Halle bzw. Gruppe, in der der Start liegt. Auf den zwei Handnetzen sind die Hallen
   die Dreiecke {{0, 1, 2}} und {{3, 4, 5}}; der Sammelpunkt 6 gehört zu keiner Halle und ist nicht als Start wählbar. **F1** misst, wie gut die gefundene Menge
   die gepflanzte trifft; **Treffer** heißt F1 mindestens 0,9.

Die Demo [Spektrale Schnitte]({URL.format("spektrale-schnitte-demo")}) führt Fiedler-Vektor, Sweep und Konduktanz für die beste Zweiteilung des **ganzen** Netzes ein.
Hier geht es um den Schritt von **global zu lokal**: eine Menge um **einen** Startplatz.
        """
    )

st.caption("🔗 Die Adresszeile oben spiegelt Ihre aktuelle Konfiguration wider – einfach kopieren, um ein Szenario zu teilen.")

load_permalink_settings()
init_session_state_defaults()

ist = st.session_state
netz_jetzt = ist["netz"]
with st.sidebar:
    sidebar_presets()  # Schnellstart oben, das aktive Preset ist hervorgehoben
    st.header("🧩 Netz")
    st.selectbox("Netz", C.NETZE, key="netz", format_func=C.NETZ_TEXT.get, help="Handnetze zum Nachrechnen, Gitterhallen im Verbund oder Zufallsgemeinschaften. Ausgegraute Regler gehören zu anderen Netzen.")
    netz_jetzt = ist["netz"]
    st.select_slider("Hallenseite a", options=C.A_STUFEN, key="a", disabled=netz_jetzt != C.NETZ_HALLEN, help="Jede Halle ist ein Gitter a×a. Nur beim Hallenverbund.")
    st.select_slider("Verbund z×z Hallen", options=C.Z_STUFEN, key="z", disabled=netz_jetzt != C.NETZ_HALLEN, help="z Hallen je Seite. Nur beim Hallenverbund.")
    st.select_slider("Gruppengröße", options=C.GROESSE_STUFEN, key="groesse", disabled=netz_jetzt != C.NETZ_GEMEIN, help="Plätze je Gruppe. Nur bei den Zufallsgemeinschaften (mit Sammelpunkten fest 60).")
    st.radio("Verbindungen nach außen je Platz (im Mittel)", C.AUSSEN_STUFEN, key="aussen", horizontal=True, disabled=netz_jetzt != C.NETZ_GEMEIN, help="Außengrad. Nur bei den Zufallsgemeinschaften.")
    st.select_slider("Plätze im Netz", options=C.N_STUFEN, key="n", disabled=netz_jetzt not in (C.NETZ_GEMEIN, C.NETZ_NADELN), format_func=E.ganz, help="Bei Zufallsgemeinschaften; auf ein Vielfaches der Gruppengröße abgerundet.")
    st.selectbox("Sammelpunkte", C.SAMMEL_ARTEN_APP, key="sammelart", format_func=C.SAMMEL_TEXT.get, disabled=netz_jetzt != C.NETZ_NADELN, help="Zusätzliche Plätze mit sehr vielen Verbindungen. Nur beim Netz mit Sammelpunkten.")
    st.header("📍 Start")
    st.selectbox("Startplatz (Handnetze)", range(6), key="start_platz", disabled=netz_jetzt not in (C.NETZ_HAND, C.NETZ_SAMMEL),
                 help="Gepflanzt ist die Halle, in der der Start liegt: {0, 1, 2} oder {3, 4, 5}. Der Sammelpunkt 6 gehört zu keiner Halle und ist nicht wählbar.")
    st.selectbox("Startplatz (Hallenverbund)", C.HALLEN_STARTS, key="start_halle", format_func=C.HALLEN_START_TEXT.get, disabled=netz_jetzt != C.NETZ_HALLEN, help="Wo in der mittleren Halle die Irrfahrt beginnt.")
    st.number_input("Zufalls-Seed", *bounds("seed"), key="seed", step=1, help="Bestimmt die Zufallsgemeinschaften samt Startplatz, den zufälligen Hallen-Startplatz und das Beispielnetz in Experiment 2.")
    st.button("🎲 Neuen Zufalls-Seed ziehen", width="stretch", on_click=randomize_seed)
    st.header("✂️ Schnittverfahren")
    st.selectbox("Verfahren oben auf der Seite", C.VERFAHREN_APP, key="verfahren", format_func=C.VERFAHREN_TEXT.get,
                 help="PageRank und gierig rechnen mit den Reglern darunter. Wärmeleitung und Breitensuche rechnen mit der für die Netzfamilie abgestimmten Einstellung (auf den Handnetzen mit einer festen Vorgabe).")
    st.select_slider("Sprungwahrscheinlichkeit β", options=C.BETA_STUFEN, key="beta", format_func=E.zahl, help="Mit dieser Wahrscheinlichkeit springt die Irrfahrt in jedem Schritt zum Start zurück.")
    st.select_slider("Push-Schwelle ε", options=C.EPS_STUFEN, key="eps", format_func=E.zahl, help="Der Push schiebt, solange ein Rest mindestens ε mal die Nachbarzahl ist. Kleiner heißt genauer und teurer.")
    st.radio("Sweep-Regel (PageRank und gierig)", C.REGELN, key="regel", format_func=C.REGEL_TEXT.get, help="min: kleinste Konduktanz. Erstes Tal: erstes Tal ab 5 Plätzen, nach dem die Konduktanz um den Faktor 1+γ steigt; sonst min.")
    st.select_slider("Schwelle γ des ersten Tals", options=C.GAMMA_STUFEN, key="gamma", format_func=lambda g: E.zahl(g), disabled=ist["regel"] == "min", help="Nur bei „erstes Tal“.")
    st.radio("Fassung der gierigen Erweiterung", tuple(C.GIERIG_TEXT), key="gierig_art", format_func=C.GIERIG_TEXT.get,
             help="Nur Gleichstandsregel und Startmenge unterscheiden die drei Fassungen. Wirkt oben (bei „gierige Erweiterung“) und in Experiment 4.")
    st.select_slider("Budget B der gierigen Erweiterung", options=C.BUDGET_STUFEN, key="budget", format_func=E.ganz, help="Volumen (Summe der Grade), bis zu dem gierig gewachsen wird.")

sync_query_params({k: ist[k] for k in SCHLUESSEL})
einst = E.Settings(**{k: ist[k] for k in SCHLUESSEL})
daten = _daten()
sz_key = (einst.netz, einst.a, einst.z, einst.groesse, einst.aussen, einst.n, einst.sammelart, einst.start_platz, einst.start_halle, einst.seed)
with st.spinner("Baue das Netz …"):
    sz = _szenario(*sz_key)
g = sz.g
if einst.netz == C.NETZ_GEMEIN and S.plaetze_gewirkt(einst.n, einst.groesse) != einst.n:
    st.info(f"Mit Gruppen zu {E.ganz(einst.groesse)} braucht es mindestens zwei Gruppen: Das Netz hat deshalb {E.ganz(g.n)} statt {E.ganz(einst.n)} Plätze.")

# --- Ergebnis ------------------------------------------------------------------------------------------------------------------------------

st.markdown("## 🎯 Die gefundene Menge")
schluessel = E.einstellung(einst, sz, daten["wahl"])
with st.spinner("Rechne den Schnitt …"):
    haupt = _schnitt(sz_key, *schluessel)
name = C.VERFAHREN_TEXT[schluessel[0]]
st.caption(f"{g.name}: {E.ganz(g.n)} Plätze, {E.ganz(g.m)} Verbindungen. Start: {sz.platz_name(sz.start)}. Verfahren: {name} ({E.einstellung_text(schluessel)})"
           + ("; auf den Handnetzen feste Vorgabe." if einst.verfahren in ("waerme", "bfs") and sz.familie is None
              else "; für diese Netzfamilie auf getrennten Netzen abgestimmt." if einst.verfahren in ("waerme", "bfs") else "."))
m1, m2, m3, m4 = st.columns(4)
m1.metric("Plätze im Schnitt", E.ganz(haupt.ergebnis.groesse), delta=f"{haupt.ergebnis.groesse - len(sz.ziel):+d} zur gepflanzten Menge", delta_color="off")
m2.metric("F1 zur gepflanzten Menge", E.de(haupt.ergebnis.f1, 2))
m3.metric("Konduktanz", E.de(haupt.konduktanz, 4), help="Randverbindungen geteilt durch das kleinere Volumen.")
m4.metric("Kantenzugriffe", E.ganz(haupt.ergebnis.zugriffe), delta=f"{E.de(haupt.ergebnis.zugriffe / g.vol, 2)}-mal die Summe aller Grade", delta_color="off")
getattr(st, E.verdikt_ergebnis(haupt, sz, name)[0])(E.verdikt_ergebnis(haupt, sz, name)[1])
art, text = E.verdikt_aufwand(haupt, sz, name)
getattr(st, art)(text)
if sz.hat_karte:
    st.plotly_chart(V.karte_menge(sz, haupt.menge), width="stretch", key="haupt_karte")
    st.caption("Rot: im Schnitt. Grün: gepflanzt, aber nicht im Schnitt. Orange: Sammelpunkt. Grau: der Rest. Der Ring markiert den Start s."
               + (" Die Karte zeigt den Block aus 3×3 Hallen um die Starthalle." if sz.netz == C.NETZ_HALLEN else ""))
elif haupt.werte:
    st.plotly_chart(V.ordnung(sz, haupt.reihe, haupt.werte, haupt.ergebnis.groesse, titel="Wert / Grad"), width="stretch", key="haupt_ordnung")
    st.caption(f"Jeder Punkt ist ein berührter Platz in der Sweep-Reihenfolge (höchstens die ersten {E.ganz(V.MAX_RANG)}). Die gestrichelte Linie ist der gewählte Schnitt.")
st.plotly_chart(V.konduktanzkurve(haupt.phis, haupt.ergebnis.groesse), width="stretch", key="haupt_konduktanz")
st.caption("Konduktanz jedes Anfangsstücks der Reihenfolge; der Punkt ist die gewählte Menge.")

# --- Kernfragen ----------------------------------------------------------------------------------------------------------------------------

st.markdown("## ❓ Kernfragen")
with st.spinner("Rechne das personalisierte PageRank …"):
    p_exakt, anteil_ziel, betas_n, anteile_n = _neustart(sz_key, einst.beta)
neu = E.Neustart(p_exakt, anteil_ziel, betas_n, anteile_n)
f1_k, f2_k, f3_k = st.columns(3)
with f1_k:
    st.markdown("**1. Was misst die Irrfahrt mit Neustart?**")
    art, text = E.verdikt_neustart(sz, einst.beta, neu)
    getattr(st, art)(text + " Mehr in Experiment 1.")
with f2_k:
    st.markdown("**2. Wie viel muss man lesen?**")
    art, text = E.verdikt_gleich_viel_kurz(daten["n_reihe"])
    getattr(st, art)(text + " Mehr in Experiment 3.")
with f3_k:
    st.markdown("**3. Welche Menge kommt heraus?**")
    zeilen = []
    regel_seite = E.regel_text(einst.regel, einst.gamma)
    for beschriftung, regel, normiert in (("p/Grad, min", "min", True), ("p/Grad, erstes Tal 0,4", "tal0.4", True),
                                          (f"p ohne Division, {E.regel_anzeige(regel_seite)}", regel_seite, False)):
        s_k = _schnitt(sz_key, "pagerank", (einst.beta, einst.eps), regel, normiert)
        zeilen.append((beschriftung, s_k.ergebnis))
    art, text = E.verdikt_ordnung_und_regel(zeilen, len(sz.ziel))
    getattr(st, art)(text + " Mehr in den Experimenten 2 und 4.")

st.markdown("---")

# --- Experiment 1 --------------------------------------------------------------------------------------------------------------------------

st.subheader("🔬 Experiment 1: Der Neustart")
st.markdown(
    f"Läuft die Irrfahrt lange, hängt ihr Aufenthaltsort kaum noch vom Start ab und sagt wenig darüber, was nah am Start liegt (auf nicht bipartiten Netzen oder in der "
    f"trägen Fassung; auf den bipartiten Gitterhallen bleibt bei der nicht trägen Irrfahrt nur die Parität des Starts erhalten). Dieses Vergessen zeigt die Demo "
    f"„Trefferzeit“ nicht (keine Mischzeit); dazu [Mischzeit exakt]({URL.format('mischzeit-exakt-demo')}) und [Meinungsbildung]({URL.format('meinungsbildung-demo')}). "
    f"Mit dem Neustart behält die Verteilung den Bezug zum Start; wie weit sie reicht, stellt β ein."
)
if sz.hat_karte:
    k1, k2 = st.columns(2)
    with k1:
        st.markdown("**PageRank p** (exakt aus dem Gleichungssystem)")
        st.plotly_chart(V.karte_werte(sz, neu.p, "p"), width="stretch", key="e1_p")
    with k2:
        st.markdown("**p geteilt durch den Grad** (die Sweep-Ordnung)")
        st.plotly_chart(V.karte_werte(sz, {u: neu.p[u] / max(g.d[u], 1) for u in S.ausschnitt(sz)}, "p/Grad"), width="stretch", key="e1_pd")
else:
    st.markdown("**p geteilt durch den Grad** nach Rang (exaktes PageRank), nach der Zielmenge gefärbt")
    werte = {u: float(neu.p[u]) for u in range(g.n) if neu.p[u] > 0}
    reihe = sorted(werte, key=lambda u: (-werte[u] / max(g.d[u], 1), u))
    st.plotly_chart(V.ordnung(sz, reihe, werte, len(sz.ziel)), width="stretch", key="e1_rang")
st.plotly_chart(V.anteil_kurve(neu.betas, neu.anteile, einst.beta), width="stretch", key="e1_anteil")
st.caption("Anteil des PageRank in der gepflanzten Menge auf diesem Netz ab diesem Start, je β (exakt gerechnet).")
art, text = E.verdikt_neustart(sz, einst.beta, neu)
getattr(st, art)(text)
art, text = E.verdikt_anteil_gemessen(daten["anteil"])
getattr(st, art)(text)

st.markdown("**Der Push, Schritt für Schritt**")
if g.n <= 10:
    protokoll, p_end, r_end, zugriffe, pushes = _protokoll(sz_key, einst.beta, einst.eps)
    if not protokoll:
        st.info("Bei dieser Schwelle ε schiebt der Push nichts: Der Rest am Start ist zu klein. Als Schnitt bleibt nur der Start.")
    else:
        if len(protokoll) > 1:
            schritt = st.slider("Push-Schritt", 1, len(protokoll), len(protokoll), key=f"e1_schritt_{len(protokoll)}")
        else:
            schritt = 1
        u_k, rest, p_k, r_k = protokoll[schritt - 1]
        st.markdown(f"Schritt {schritt} von {E.ganz(pushes)}: Platz **{u_k}** schiebt den Rest {E.de(rest, 4)}. Davon bleiben β = {E.zahl(einst.beta)} bei p, "
                    f"der Rest geht gleich an seine {g.d[u_k]} Nachbarn.")
        st.dataframe(pd.DataFrame({"Platz": range(g.n), "Nachbarn (Grad)": g.d, "p": [round(p_k.get(u, 0.0), 6) for u in range(g.n)],
                                   "Rest r": [round(r_k.get(u, 0.0), 6) for u in range(g.n)], "Schwelle ε·Grad": [round(einst.eps * g.d[u], 6) for u in range(g.n)]}),
                     hide_index=True, width="stretch")
        abweichung = E.invariante_abweichung(sz, einst.beta, p_k, r_k)
        st.caption(f"Invariante: p plus das PageRank, das aus dem Rest noch entsteht, ist das gesuchte PageRank. Größte Abweichung nach diesem Schritt: {abweichung:.1e}. "
                   f"Insgesamt {E.anzahl(pushes, 'Push', 'Pushes')} mit {E.anzahl(zugriffe, 'Kantenzugriff', 'Kantenzugriffen')} "
                   f"(Obergrenze 1/(β·ε) = {E.ganz(1 / (einst.beta * einst.eps))})."
                   + (f" Der Regler zeigt nur die ersten {len(protokoll)} Pushes." if pushes > len(protokoll) else ""))
else:
    pushes, zugriffe, beruehrt = _push_zaehlung(sz_key, einst.beta, einst.eps)
    st.markdown(f"Der Push mit β = {E.zahl(einst.beta)} und ε = {E.zahl(einst.eps)} macht hier **{E.anzahl(pushes, 'Push', 'Pushes')}** mit "
                f"**{E.anzahl(zugriffe, 'Kantenzugriff', 'Kantenzugriffen')}** und berührt {E.ganz(beruehrt)} von {E.ganz(g.n)} Plätzen. Obergrenze: 1/(β·ε) = {E.ganz(1 / (einst.beta * einst.eps))}. "
                f"Schritt für Schritt nachvollziehbar ist er auf den beiden Handnetzen.")

st.markdown("---")

# --- Experiment 2 --------------------------------------------------------------------------------------------------------------------------

st.subheader("🔬 Experiment 2: Durch den Grad teilen")
st.markdown("Ein **Sammelpunkt** ist ein Platz mit sehr vielen Verbindungen. Er sammelt viel PageRank, ohne dass er zur Gemeinschaft des Starts gehört. "
            "Der Sweep ordnet deshalb nach p/Grad. Hier wird derselbe Push zweimal geschnitten: nach p/Grad und nach p allein.")
c1, c2, c3 = st.columns(3)
art_e2 = c1.selectbox("Bauart", ("nah", "fern40", "fern200", "ohne"), key="e2_art", format_func=C.SAMMEL_TEXT.get)
eps_e2 = c2.radio("ε", M.SAMMEL_EPS, index=1, key="e2_eps", format_func=E.zahl, horizontal=True)
regel_e2 = c3.selectbox("Sweep-Regel", M.SAMMEL_REGELN, index=2, key="e2_regel", format_func=E.regel_anzeige)
mit = E.sammel_zeile(daten, art_e2, eps_e2, "p/Grad", regel_e2)
ohne = E.sammel_zeile(daten, art_e2, eps_e2, "p", regel_e2)
art, text = E.verdikt_gradfalle(mit, ohne, art_e2, eps_e2, regel_e2)
getattr(st, art)(text)
st.dataframe(pd.DataFrame([
    {"Ordnung": o, "F1-Median": round(z["median"], 3), "F1-Mittel": round(z["mittel"], 3), "Netze mit F1 < 0,8": z["unter08"], "Treffer (F1 ≥ 0,9)": z["treffer"],
     "Sammelpunkte im Schnitt (Mittel)": round(z["sammel_mittel"], 2), "Plätze im Schnitt (Median)": z["groesse"]} for o, z in (("p/Grad", mit), ("p", ohne))]),
    hide_index=True, width="stretch")
st.plotly_chart(V.verteilung(mit, ohne), width="stretch", key="e2_verteilung")
st.caption(f"Vorgerechnet: {M.SAMMEL_NETZE} Netze je Bauart mit {E.ganz(M.N_STANDARD)} Plätzen, Gruppen zu {M.SAMMEL_GRUPPE}, Außengrad 1, β = {E.zahl(M.SAMMEL_BETA)}.")
zellen_f, besser_f, schlechter_f = E.zaehle_gradfalle(daten)
st.markdown(f"Über alle Bauarten mit Sammelpunkten, ε und Regeln ({zellen_f} Kombinationen): nach p/Grad liegt der Median in **{besser_f}** davon um mehr als 0,05 höher als "
            f"nach p, in **{schlechter_f}** um mehr als 0,05 niedriger. Wie stark es schadet, hängt an Sweep-Regel und ε. " + E.gradfalle_hinweis(daten))
if st.toggle("Ein Netz dieser Bauart ansehen (Zufalls-Seed der Seitenleiste)", key="e2_live"):
    live_key = (C.NETZ_NADELN, einst.a, einst.z, 60, 1, M.N_STANDARD, art_e2 if art_e2 != "ohne" else "nah", 0, einst.start_halle, einst.seed)
    if art_e2 == "ohne":
        live_key = (C.NETZ_GEMEIN, einst.a, einst.z, 60, 1, M.N_STANDARD, "nah", 0, einst.start_halle, einst.seed)
    with st.spinner("Baue das Netz mit 16 000 Plätzen …"):
        sz_live = _szenario(*live_key)
    spalten = st.columns(2)
    for spalte, normiert, titel in ((spalten[0], True, "p / Grad"), (spalten[1], False, "p")):
        s_l = _schnitt(live_key, "pagerank", (M.SAMMEL_BETA, eps_e2), regel_e2, normiert)
        with spalte:
            st.markdown(f"**nach {titel}**: {E.anzahl(s_l.ergebnis.groesse, 'Platz', 'Plätze')}, F1 {E.de(s_l.ergebnis.f1, 2)}, davon Sammelpunkte {len(set(s_l.menge) & sz_live.sammel)}")
            st.plotly_chart(V.ordnung(sz_live, s_l.reihe, s_l.werte, s_l.ergebnis.groesse, normiert=normiert, titel=titel), width="stretch", key=f"e2_ordnung_{normiert}")
st.markdown("**Von Hand:** Im Netz „Halle mit Sammelpunkt“ (Platz 6 ist mit 0, 1, 3, 4, 5 verbunden, β = 1/4, ab Platz 0) steht der Sammelpunkt nach p auf Rang 2. "
            "Der Sweep nach p/Grad wählt {0, 1, 2} mit Konduktanz 1/3, der Sweep nach p {0, 1, 2, 6} mit 2/5. Im Netz „Zwei Hallen“ ohne Sammelpunkt finden beide "
            "Ordnungen dieselbe Halle. Chen, Zhang und Rohe (arXiv 1910.12937, hier nur nach der Zusammenfassung wiedergegeben) beschreiben für das gradkorrigierte "
            "Blockmodell, dass unbereinigtes PageRank hochgradige Knoten außerhalb des Startblocks bevorzuge; eine Gradanpassung halte die Menge näher am Start, und "
            "bereinigte und unbereinigte Fassung ergänzten sich.")

st.markdown("---")

# --- Experiment 3 --------------------------------------------------------------------------------------------------------------------------

st.subheader("🔬 Experiment 3: Gleich viel gelesen")
st.markdown("Wächst das Netz, während die Gemeinschaften gleich groß bleiben: Wie viel muss man lesen? Zufallsgemeinschaften (Gruppen zu 60, Außengrad 1), "
            f"je {M.N_REIHE_NETZE} Netze, vorgerechnet.")
weitere = st.checkbox("Auch den abgestimmten PageRank und die träge Fassung zeigen", key="e3_weitere")
namen = ["push", "gierig", "waerme"] + (["abgestimmt", "push_traege"] if weitere else [])
st.plotly_chart(V.aufwand_gegen_n(daten["n_reihe"], namen, 1 / (M.PUSH_VORFUEHRUNG[0] * M.PUSH_VORFUEHRUNG[1])), width="stretch", key="e3_aufwand")
st.caption("Obergrenze: 1/(β·ε) für den Push mit β = 0,006 und ε = 3·10⁻⁴. Die anderen Kurven haben eigene Einstellungen (Tabelle).")
st.dataframe(pd.DataFrame(E.tabelle_n(daten, namen)), hide_index=True, width="stretch")
art, text = E.verdikt_gleich_viel(daten["n_reihe"], *M.PUSH_VORFUEHRUNG)
getattr(st, art)(text)
st.markdown(E.verbund_text(daten))
st.markdown(E.fiedler_text(daten))

st.markdown("---")

# --- Experiment 4 --------------------------------------------------------------------------------------------------------------------------

st.subheader("🔬 Experiment 4: Welche Größe findet man?")
sz4_key = sz_key if einst.netz == C.NETZ_HALLEN else (C.NETZ_HALLEN, 8, 8, 60, 1, M.N_STANDARD, "nah", 0, "mitte", einst.seed)
with st.spinner("Baue den Hallenverbund …"):
    sz4 = _szenario(*sz4_key)
st.markdown(f"Im Hallenverbund gibt es Gemeinschaften auf mehreren Größen: eine Halle, zwei Nachbarhallen, einen Block aus 2×2 Hallen. "
            f"Netz dieses Experiments: {sz4.g.name}, Start {sz4.platz_name(sz4.start)}"
            + ("." if einst.netz == C.NETZ_HALLEN else " (wählen Sie in der Seitenleiste „Hallenverbund“, um a, z und Start zu ändern)."))
stufen = E.treppe(sz4.g, sz4.z, sz4.a)
sp = st.columns(3)
for spalte, s_t in zip(sp, stufen):
    spalte.metric(f"{s_t['name']} ({s_t['plaetze']} Plätze)", f"{s_t['rand']}/{E.ganz(s_t['volumen'])}", help=f"Konduktanz {E.de(s_t['konduktanz'], 4)} (Randverbindungen/Volumen).")
art, text = E.verdikt_treppe(stufen)
getattr(st, art)(text)
regel_wahl = E.regel_text(einst.regel, einst.gamma)
pr_wahl = _schnitt(sz4_key, "pagerank", (einst.beta, einst.eps), regel_wahl)
st.plotly_chart(V.konduktanzkurve(pr_wahl.phis, pr_wahl.ergebnis.groesse, marken=[(s_t["plaetze"], s_t["konduktanz"], s_t["name"]) for s_t in stufen],
                                  laenge=min(len(pr_wahl.phis), 6 * sz4.a * sz4.a)), width="stretch", key="e4_kurve")
st.caption("Konduktanzkurve entlang der PageRank-Ordnung (β und ε der Seitenleiste), bis sechs Hallengrößen. Rauten: die drei Blöcke oben (als ganze Hallen, nicht als Anfangsstücke der Ordnung).")
zeilen_e4 = []
for titel, schluessel4 in (("PageRank, min", ("pagerank", (einst.beta, einst.eps), "min")),
                           (f"PageRank, erstes Tal {E.zahl(einst.gamma)}", ("pagerank", (einst.beta, einst.eps), f"tal{einst.gamma:g}")),
                           (C.VERFAHREN_TEXT[einst.gierig_art] + ", min", (einst.gierig_art, einst.budget, "min")),
                           (C.VERFAHREN_TEXT[einst.gierig_art] + f", erstes Tal {E.zahl(einst.gamma)}", (einst.gierig_art, einst.budget, f"tal{einst.gamma:g}"))):
    s4 = _schnitt(sz4_key, *schluessel4)
    zeilen_e4.append({"Verfahren": titel, "Plätze im Schnitt": s4.ergebnis.groesse, "davon aus der Starthalle": len(set(s4.menge) & sz4.ziel),
                      "F1 zur Starthalle": round(s4.ergebnis.f1, 3), "Konduktanz": round(s4.konduktanz, 5), "Kantenzugriffe": s4.ergebnis.zugriffe})
st.dataframe(pd.DataFrame(zeilen_e4), hide_index=True, width="stretch")
haupt4 = _schnitt(sz4_key, "pagerank", (einst.beta, einst.eps), regel_wahl)
st.plotly_chart(V.karte_menge(sz4, haupt4.menge), width="stretch", key="e4_karte")
st.caption(f"Menge des PageRank-Schnitts mit der Regel der Seitenleiste ({E.regel_anzeige(regel_wahl)}). Die Karte zeigt den Block aus 3×3 Hallen um die Starthalle.")

st.markdown("**Vorgerechnet: dieselbe Rechnung, nur Regel oder ε geändert**")
f_c1, f_c2 = st.columns(2)
fall_e4 = f_c1.selectbox("Fall", tuple(M.REGEL_FAELLE), key="e4_fall", format_func=E.FALL_TEXT.get)
eps_e4 = f_c2.radio("ε in dieser Tabelle", M.REGEL_EPS, index=1, key="e4_eps", format_func=E.zahl, horizontal=True)
art, text = E.verdikt_regel(daten, fall_e4, eps_e4)
getattr(st, art)(text)
st.dataframe(pd.DataFrame(E.tabelle_regel(daten, fall_e4)), hide_index=True, width="stretch")
art, text = E.verdikt_nur_eps(daten)
getattr(st, art)(text)

st.markdown("**Die Falle beim gierigen Verfahren: der Gleichstand**")
gleich = E.gleichstandsbeispiel()
g1, g2 = st.columns(2)
g1.metric("Gleichstand „kleinerer Grad, dann Nummer“", f"{gleich['gierig-grad'][0]} Plätze", delta=f"davon {gleich['gierig-grad'][1]} aus der Starthalle", delta_color="off")
g2.metric("Gleichstand „zuerst entdeckt“", f"{gleich['gierig-entdeckt'][0]} Plätze", delta=f"davon {gleich['gierig-entdeckt'][1]} aus der Starthalle", delta_color="off")
st.markdown("Hallenverbund 3×3 mit Hallen 6×6, Start Platz (2,2) der mittleren Halle, Budget 400, erstes Tal 0,4: Nur die Gleichstandsregel unterscheidet die beiden Läufe. "
            "Im Gitter können Randplätze denselben Anteil ihrer Verbindungen in der Menge haben; dann entscheidet die Gleichstandsregel. Auf den Testhallen in Experiment 5 liegen die beiden Fassungen mit ihren Haupteinstellungen weit auseinander (F1-Median bei „kleinerem Grad“ 0,67).")

st.markdown("---")

# --- Experiment 5 --------------------------------------------------------------------------------------------------------------------------

st.subheader("🔬 Experiment 5: Die Gegner")
st.markdown("Jedes Verfahren wurde auf getrennten Netzen abgestimmt und dann auf neuen Netzen geprüft. Je Verfahren und Sweep-Familie gewann das höchste mittlere F1; "
            "innerhalb von 0,005 davon die sparsamste Einstellung. ★ markiert die Haupteinstellung (die auf den Abstimm-Netzen bessere Sweep-Familie). "
            "Alle gierigen Regeln, der Nachbarschafts-Start und das „erste Tal“ entstanden erst nach Blick auf Ergebnisse; hier sind sie auf neuen Zufalls-Seeds gemessen.")
fam_standard = M.FAMILIEN.index(sz.familie) if sz.familie in M.FAMILIEN else 0
h1, h2 = st.columns(2)
familie_e5 = h1.selectbox("Netzfamilie der Tabelle", M.FAMILIEN, index=fam_standard, key="e5_familie", format_func=M.FAMILIE_TEXT.get)
beide = h2.checkbox("Beide Sweep-Familien zeigen", key="e5_beide")
st.dataframe(pd.DataFrame(E.tabelle_test(daten, familie_e5, sweeps_alle=beide)), hide_index=True, width="stretch")
st.caption(("Zellen: Hallenseite a (Verbund 8×8, alle Startplätze der mittleren Halle)." if familie_e5 == "hallen" else
            f"Zellen: Gruppengröße (je {M.NETZE_TEST} neue Netze mit {E.ganz(M.N_STANDARD)} Plätzen).")
           + " Je Zelle F1-Median / F1-Mittel / Treffer. „außerhalb“: nicht in der Abstimmung."
           + (" Für die abgestimmten Hallenseiten ist der Test keine unabhängige Prüfung: um eine innere Halle sind Abstimm- und Testverbund gleich aufgebaut." if familie_e5 == "hallen" else ""))
st.markdown(E.netzgroessen_text(daten, familie_e5))
z_alle = E.zaehlungen(daten)
art, text = E.verdikt_gegner(z_alle["pagerank_tal"])
getattr(st, art)(text)
art, text = E.verdikt_zuverlaessigkeit(daten, z_alle)
getattr(st, art)(text)
st.markdown(E.sparsamste_und_lokal_text(daten))
st.markdown("**Ein Netz zum Ansehen:** alle Verfahren mit den abgestimmten Einstellungen der Netzfamilie auf dem Netz der Seitenleiste.")
if sz.familie is None:
    st.info("Für die Handnetze gibt es keine abgestimmten Einstellungen; wählen Sie in der Seitenleiste Hallenverbund oder Zufallsgemeinschaften.")
elif st.button("Alle Verfahren auf diesem Netz rechnen", key="e5_rechnen") or st.session_state.get("e5_fuer") == sz_key:
    st.session_state["e5_fuer"] = sz_key
    with st.spinner("Rechne alle Verfahren (meist unter einer Sekunde) …"):
        st.dataframe(pd.DataFrame(_live(sz_key)), hide_index=True, width="stretch")
    st.caption("Ein einzelnes Netz: Der Erfolg ist oft zweigipflig, ein Lauf sagt wenig über die Verfahren.")

st.markdown("---")

# --- Grenzen -------------------------------------------------------------------------------------------------------------------------------

st.subheader("🚧 Wo die Annahmen enden")
st.markdown(
    f"""
* **Zwei verschiedene Rücksprünge:** Die Demo „Überdeckungszeit“ benutzt einen **festen Rücksprung alle τ Schritte** (der Sprung zählt nicht als Schritt). Diese Demo benutzt
  einen **zufälligen Neustart mit Sprungwahrscheinlichkeit**; er ist ein anderes Verfahren. Ergebnisse des einen gelten für den anderen nicht ohne eigene Messung.
* **Gemessen sind nur synthetische, ungewichtete, ungerichtete Netze:** Gitterhallen und Zufallsgemeinschaften. Netze mit Ortsbezug, echte oder gewichtete Netze sind nicht gemessen.
* **Gerichtetes PageRank** rechnet die Demo nicht; dazu [Zentralität]({URL.format("centrality-demo")}) (PageRank auf dem ungerichteten Netz) und
  [interne Verlinkung]({URL.format("interne-verlinkung-demo")}) (gerichtet). Eine Link-Vorhersage ist hier kein Experiment; dazu [Link-Vorhersage]({URL.format("link-prediction-demo")}).
* **Eine Gemeinschaft, nicht alle:** Gesucht ist nur die Gemeinschaft **eines** Startplatzes. Gemeinschaften für das ganze Netz zeigen [Leiden]({URL.format("leiden-demo")}) und
  [stochastisches Blockmodell]({URL.format("stochastic-block-demo")}).
* **Weitere Gegner sind nicht gemessen:** gieriges Verfahren mit Entfernen von Plätzen, Fluss-Verfahren, Nibble, Louvain oder Leiden von einem Start, hk-relax von Kloster und Gleich.
* **Bezug zum Betrieb:** Empfehlungen mit Irrfahrten mit Neustart sind für den Betrieb beschrieben (Twitter: Gupta u. a., WWW 2013; Pinterest Pixie: Eksombatchai u. a., WWW 2018).
  Das stützt den **Neustart**, nicht den lokalen Schnitt, den diese Demo misst.
"""
)

st.markdown("---")

with st.expander("⚠️ Annahmen, Grenzen und bekannte Probleme"):
    st.markdown(E.ANNAHMEN_MARKDOWN)

# --- Formeln -------------------------------------------------------------------------------------------------------------------------------

with st.expander("📐 Mathematische Formulierung"):
    st.markdown(
        r"""
**Lesehilfe.** Gegeben ist ein einfaches, ungerichtetes Netz mit $n$ Plätzen und $m$ Verbindungen, ein Startplatz $s$ und die Sprungwahrscheinlichkeit $\beta$. Gesucht ist
eine Menge um $s$. Bewertet wird sie auf diesen Testnetzen gegen eine gepflanzte Menge $C$.

| Symbol | Bedeutung |
|---|---|
| $d_u$, $m$ | Nachbarzahl (Grad) von $u$, Zahl der Verbindungen |
| $P$ | Übergangsmatrix der Irrfahrt: $P_{uv} = 1/d_u$ für Nachbarn, sonst 0 |
| $e_s$ | Zeilenvektor, 1 an der Stelle $s$ |
| $p$ | personalisiertes PageRank ab $s$ |
| $r$ | Rest des Push |
| $\varepsilon$ | Push-Schwelle |
| $\mathrm{vol}(S)$ | Summe der Grade in $S$ |
| $\partial(S)$ | Zahl der Verbindungen zwischen $S$ und dem Rest |

**Personalisiertes PageRank** (Zeilenvektor, nicht träge Irrfahrt):

$$
p = \beta\, e_s + (1-\beta)\, p\, P
$$

Mit $y_u = p_u / d_u$ ist das ein symmetrisches, positiv definites Gleichungssystem ($A$ Adjazenzmatrix, $D$ Diagonalmatrix der Grade); so rechnet die Demo die exakten Werte:

$$
\bigl(D - (1-\beta) A\bigr)\, y = \beta\, e_s^{\top}
$$

**Push.** Solange $r_u \ge \varepsilon d_u$ (Warteschlange, Anfang $s$, $r = e_s$, $p = 0$):

$$
p_u \leftarrow p_u + \beta\, r_u
$$

$$
r_v \leftarrow r_v + \frac{(1-\beta)\, r_u}{d_u} \quad (v \sim u)
$$

$$
r_u \leftarrow 0
$$

Nach jedem Schritt gilt $p + \mathrm{ppr}(r) = \mathrm{ppr}(e_s)$; am Ende ist $0 \le \mathrm{ppr}_u - p_u \le \varepsilon d_u$, und die Summe der Grade aller Pushes ist höchstens
$1/(\beta\varepsilon)$ (jeder Push überführt mindestens $\beta\,\varepsilon\, d_u$ von $r$ nach $p$).

**Träge Fassung (nur Fachteil).** Andersen, Chung und Lang rechnen mit der trägen Irrfahrt $W = (I+P)/2$ und der Sprungwahrscheinlichkeit

$$
\alpha = \frac{\beta}{2 - \beta}
$$

Dann hat $p = \alpha\, e_s + (1-\alpha)\, p\, W$ dieselbe Lösung. Zur Einordnung: `networkx.pagerank` nennt `alpha` den Anteil **ohne** Sprung, also $1 - \beta$.

**Sweep und Konduktanz.** Plätze nach $p_u/d_u$ absteigend ordnen, bei Gleichstand nach Nummer. Für jedes Anfangsstück $S$:

$$
\Phi(S) = \frac{\partial(S)}{\min\bigl(\mathrm{vol}(S),\; 2m - \mathrm{vol}(S)\bigr)}
$$

**F1** gegen die gepflanzte Menge $C$:

$$
F_1 = \frac{2\, |S \cap C|}{|S| + |C|}
$$

**Wärmeleitung** (eigene Fassung): Reihe bis zum Rest höchstens $10^{-3}$, je Schritt werden Einträge unter $\delta d_u$ nicht weitergegeben.

$$
h = \sum_{k \ge 0} e^{-t} \frac{t^k}{k!}\, e_s P^k
$$

**Gütezusage von Andersen, Chung und Lang** (Satz 5 der Langfassung, in der trägen Fassung mit $\alpha$). Voraussetzungen: $\Phi(C) \le \alpha/10$, $\mathrm{vol}(C) \le \tfrac23\, 2m$,
Start in einer Teilmenge von $C$ mit mindestens halbem Volumen (also nicht für jeden Startplatz in $C$) und $\varepsilon \le 1/(10\,\mathrm{vol}(C))$. Der Beweis liefert für den Sweep

$$
\Phi < \sqrt{90\, \alpha \ln\bigl(30 \sqrt{\mathrm{vol}(C)}\bigr)}
$$

(die Fassung nennt keine Basis des Logarithmus; hier der natürliche).
        """
    )
    st.markdown(E.acl_text())
    st.markdown(
        r"""
**Literatur.** R. Andersen, F. Chung, K. Lang, *Using PageRank to Locally Partition a Graph*, Langfassung (2006), Satz 5 samt Beweis gelesen
([PDF](https://fanchung.ucsd.edu/wp/localpartfull.pdf)). Nur nach Zusammenfassungen wiedergegeben: J. Leskovec, K. Lang, A. Dasgupta, M. Mahoney (arXiv 0810.1355),
dass in über 100 großen Netzen die nach Konduktanz besten Gemeinschaften klein seien und größere im Kern aufgingen; F. Chen, Y. Zhang, K. Rohe (arXiv 1910.12937) zur
Gradanpassung; K. Kloster, D. Gleich (arXiv 1403.3148) zu lokaler Wärmeleitung (ihr Verfahren ist hier nicht nachgebaut).
        """
    )

st.markdown("---")
st.caption(
    "Diese Demo ist Teil des Portfolios von [Sebastian Hanisch](https://sebastianhanisch.net) – "
    "Operations Research und Machine Learning ([Über mich](https://sebastianhanisch.net/ueber-mich.html)). "
    "Mehr zur Reihe: [Irrfahrten auf Netzen: Trefferzeit bis Schnitt](https://sebastianhanisch.net/konzepte-irrfahrten.html)."
)
