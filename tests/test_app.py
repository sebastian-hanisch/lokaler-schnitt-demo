"""End-to-end-Tests mit Streamlits AppTest: Standard, jedes Preset mit seiner Verdikt-Zeile, jeder Knopf, Regler an den Rändern, Permalink, alle fünf Experimente."""

import os
from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest

import lsn_constants as C

APP = str(Path(__file__).resolve().parent.parent / "app.py")
TIMEOUT = int(os.environ.get("APPTEST_TIMEOUT", "300"))


def _app(**query) -> AppTest:
    at = AppTest.from_file(APP, default_timeout=TIMEOUT)
    for k, v in query.items():
        at.query_params[k] = str(v)
    at.run()
    _ohne_fehler(at)
    return at


def _ohne_fehler(at):
    assert not at.exception, [str(e) for e in at.exception]
    assert not at.error, [e.value for e in at.error]


def _meldungen(at):
    return [(art, m.value) for art, liste in (("success", at.success), ("info", at.info), ("warning", at.warning)) for m in liste]


def _preset(at, name):
    at.sidebar.button(key=f"preset_{name}").click().run()
    _ohne_fehler(at)
    return at


def test_standard_zeigt_alle_experimente_und_den_handschnitt():
    at = _app()
    assert [s.value for s in at.subheader if s.value.startswith("🔬")] == [
        "🔬 Experiment 1: Der Neustart", "🔬 Experiment 2: Durch den Grad teilen", "🔬 Experiment 3: Gleich viel gelesen",
        "🔬 Experiment 4: Welche Größe findet man?", "🔬 Experiment 5: Die Gegner"]
    assert at.metric[0].label == "Plätze im Schnitt" and at.metric[0].value == "3"
    assert at.metric[1].value == "1,00"
    assert any("16/19" in w for _, w in _meldungen(at))
    assert len(at.dataframe) >= 5


@pytest.mark.parametrize("name, art, teil", [
    ("Von Hand: Neustart auf zwei Hallen", "success", "findet 3 Plätze (gepflanzt: 3), F1 = 1,00"),
    ("Falle: Sammelpunkt", "success", "Treffer (F1 ≥ 0,9)"),
    ("Hallenverbund 8×8", "success", "findet 64 Plätze (gepflanzt: 64)"),
    ("Welche Größe?", "warning", "deutlich größer als die gepflanzte"),
    ("Unbekannte Größe, Außengrad 3", "warning", "Kein Treffer"),
])
def test_jedes_preset_mit_seiner_verdikt_zeile(name, art, teil):
    at = _preset(_app(), name)
    treffer = [a for a, w in _meldungen(at) if w.startswith("PageRank (Push) mit Sweep findet") and teil in w]
    assert treffer == [art], [w for _, w in _meldungen(at) if "findet" in w]


@pytest.mark.parametrize("verfahren", C.VERFAHREN_APP)
@pytest.mark.parametrize("preset", ["Von Hand: Neustart auf zwei Hallen", "Hallenverbund 8×8", "Falle: Sammelpunkt"])
def test_jedes_verfahren_auf_den_netzen(verfahren, preset):
    at = _preset(_app(), preset)
    at.sidebar.selectbox(key="verfahren").set_value(verfahren).run()
    _ohne_fehler(at)
    assert at.metric[0].label == "Plätze im Schnitt"


def test_jeder_knopf():
    at = _app()
    labels = [b.label for b in at.button]
    for i, label in enumerate(labels):
        at = _app()
        at.button[i].click().run()
        _ohne_fehler(at)


@pytest.mark.parametrize("netz", C.NETZE)
def test_jedes_netz(netz):
    at = _app()
    at.sidebar.selectbox(key="netz").set_value(netz).run()
    _ohne_fehler(at)


@pytest.mark.parametrize("query", [
    {"netz": "hallen", "a": 20, "z": 16, "beta": 0.00075, "eps": 1.5e-5},
    {"netz": "hallen", "a": 4, "z": 4, "beta": 0.5, "eps": 0.05, "budget": 14, "regel": "tal", "gamma": 1.6},
    {"netz": "gemein", "n": 960, "g": 960, "aussen": 3, "beta": 0.5, "eps": 0.05},
    {"netz": "gemein", "n": 16000, "g": 20, "aussen": 3, "beta": 0.00075, "eps": 1.5e-5, "budget": 28000},
    {"netz": "gemein_sammel", "sammel": "fern200", "n": 960, "seed": 999999, "verfahren": "bfs"},
    {"netz": "hand", "beta": 0.00075, "eps": 1.5e-5, "start": 5},
    {"netz": "sammel", "beta": 0.5, "eps": 0.05, "start": 3, "verfahren": "waerme"},
])
def test_raender(query):
    at = _app(**query)
    assert at.metric[0].label == "Plätze im Schnitt"


def test_permalink_wird_uebernommen_und_begrenzt():
    at = _app(netz="hallen", a=10, z=4, beta=0.015, eps=0.001, regel="min", seed=10 ** 9, hstart="ecke", gierig="gierig-grad", budget=600)
    ss = at.session_state
    assert (ss["netz"], ss["a"], ss["z"], ss["beta"], ss["eps"], ss["start_halle"], ss["gierig_art"], ss["budget"]) == (
        "hallen", 10, 4, 0.015, 0.001, "ecke", "gierig-grad", 600)
    assert ss["seed"] == C.SEED_MAX
    assert at.query_params["netz"] in ("hallen", ["hallen"])


def test_permalink_unsinn_wird_verworfen():
    at = _app(netz="nichts", a=7, beta="abc", seed="x")
    assert at.session_state["netz"] == "hand" and at.session_state["a"] == 8


def test_push_schritt_regler_auf_dem_handnetz():
    at = _app()
    regler = next(s for s in at.main.slider if s.label == "Push-Schritt")
    assert regler.max == 8
    regler.set_value(1).run()
    _ohne_fehler(at)
    assert any("Schritt 1 von 8" in m.value and "Platz **0**" in m.value for m in at.markdown)


def test_push_ohne_schritt():
    at = _app(netz="hand", eps=0.05, beta=0.25)
    at.sidebar.select_slider(key="eps").set_value(0.05).run()
    _ohne_fehler(at)


def test_experiment_2_alle_auswahlen_und_livenetz():
    at = _app()
    for art in ("ohne", "fern40", "fern200", "nah"):
        at.main.selectbox(key="e2_art").set_value(art).run()
        _ohne_fehler(at)
    for eps in (1e-4, 1e-3):
        at.main.radio(key="e2_eps").set_value(eps).run()
        _ohne_fehler(at)
    at.main.toggle(key="e2_live").set_value(True).run()
    _ohne_fehler(at)
    assert any("nach p / Grad" in m.value for m in at.markdown)


def test_experimente_3_4_5():
    at = _app()
    at.main.checkbox(key="e3_weitere").check().run()
    _ohne_fehler(at)
    for fall in ("hallen16", "a3_120", "a3_480"):
        at.main.selectbox(key="e4_fall").set_value(fall).run()
        _ohne_fehler(at)
    for familie in ("a1", "a3", "hallen"):
        at.main.selectbox(key="e5_familie").set_value(familie).run()
        _ohne_fehler(at)
    at.main.checkbox(key="e5_beide").check().run()
    _ohne_fehler(at)
    at = _preset(at, "Hallenverbund 8×8")
    at.main.button(key="e5_rechnen").click().run()
    _ohne_fehler(at)
    assert any("Anteil an 2m" in str(d.value.columns.tolist()) for d in at.dataframe)


def test_experiment_4_nimmt_den_verbund_der_seitenleiste():
    at = _app(netz="hallen", a=6, z=4)
    assert any("Hallenverbund 4×4, Hallen 6×6" in m.value for m in at.markdown)
