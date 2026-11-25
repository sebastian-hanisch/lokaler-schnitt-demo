"""Layout (DEMO-PLAYBOOK §2): fester Kopf, Schnellstart oben in der Seitenleiste, aktives Preset hervorgehoben.

Die Hervorhebung ist zustandslos (`aktives_preset` vergleicht jeden Regler aus SETTING_SPECS mit dem Preset). Der Test unten stellt
sicher, dass wirklich JEDER Regler der Seitenleiste dort steht: sonst bliebe das Preset trotz Änderung markiert."""

from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest

import lsn_constants as C
import lsn_presets as P

APP = str(Path(__file__).resolve().parent.parent / "app.py")
REGLER_ARTEN = ("slider", "number_input", "select_slider", "selectbox", "radio", "toggle", "checkbox", "text_input")


def _app() -> AppTest:
    at = AppTest.from_file(APP, default_timeout=180)
    at.run()
    assert not at.exception, [str(e) for e in at.exception]
    return at


def _typen(at) -> dict:
    """Button-Typ je Preset-Name (die Preset-Buttons der Seitenleiste)."""
    return {b.label: b.proto.type for b in at.sidebar.button if b.label in C.PRESETS}


def _regler(at, key):
    for art in REGLER_ARTEN:
        try:
            return getattr(at.sidebar, art)(key=key)
        except KeyError:
            continue
    raise AssertionError(f"Regler {key} steht nicht in der Seitenleiste")


def test_presets_stehen_in_der_seitenleiste_und_nicht_im_hauptbereich():
    at = _app()
    assert [b.label for b in at.sidebar.button][: len(C.PRESETS)] == list(C.PRESETS)  # die ersten Buttons der Seitenleiste
    assert not [b for b in at.main.button if b.label in C.PRESETS]


def test_titel_steht_im_festen_kopf():
    at = _app()
    assert "st-key-kopf" in " ".join(h.proto.body for h in at.get("html"))  # das Stylesheet setzt an der Klasse des Containers an
    assert at.title[0].value


def test_beim_start_ist_genau_das_standard_preset_hervorgehoben():
    typen = _typen(_app())
    assert [name for name, typ in typen.items() if typ == "primary"] == [next(iter(C.PRESETS))]


@pytest.mark.parametrize("name", list(C.PRESETS))
def test_angeklicktes_preset_ist_hervorgehoben_und_bleibt_es_im_naechsten_lauf(name):
    at = _app()
    at.sidebar.button(key=f"preset_{name}").click().run()
    assert [n for n, typ in _typen(at).items() if typ == "primary"] == [name]
    at.run()
    assert [n for n, typ in _typen(at).items() if typ == "primary"] == [name]


def test_jeder_regler_der_seitenleiste_steht_in_setting_specs():
    at = _app()
    schluessel = {w.key for art in REGLER_ARTEN for w in getattr(at.sidebar, art) if w.key}
    fehlt = schluessel - set(P.SETTING_SPECS)
    assert not fehlt, f"Regler {sorted(fehlt)} fehlen in SETTING_SPECS: ihre Änderung hebt das aktive Preset nicht auf"


# ausgegraute Regler lassen sich nicht bedienen: je Regler ein Preset, in dem er aktiv ist
PRESET_FUER = {"a": "Hallenverbund 8×8", "z": "Hallenverbund 8×8", "start_halle": "Hallenverbund 8×8", "gamma": "Hallenverbund 8×8",
               "groesse": "Unbekannte Größe, Außengrad 3", "aussen": "Unbekannte Größe, Außengrad 3", "n": "Unbekannte Größe, Außengrad 3",
               "sammelart": "Falle: Sammelpunkt"}


@pytest.mark.parametrize("state_key", list(P.SETTING_SPECS))
def test_jede_aenderung_eines_reglers_hebt_die_hervorhebung_auf(state_key):
    at = _app()
    name = PRESET_FUER.get(state_key, next(iter(C.PRESETS)))
    at.sidebar.button(key=f"preset_{name}").click().run()
    spec = P.SETTING_SPECS[state_key]
    jetzt = at.session_state[state_key]
    if spec.options is not None:
        neu = next(o for o in reversed(spec.options) if o != jetzt)
    else:
        neu = spec.hi if jetzt != spec.hi else spec.lo
    _regler(at, state_key).set_value(neu).run()
    assert not at.exception, [str(e) for e in at.exception]
    assert at.session_state[state_key] == neu
    assert "primary" not in _typen(at).values()
    # erneutes Anklicken markiert wieder
    at.sidebar.button(key=f"preset_{name}").click().run()
    assert _typen(at)[name] == "primary"


def test_ausgegraute_regler_folgen_dem_netz():
    at = _app()
    assert _regler(at, "a").disabled and _regler(at, "sammelart").disabled and not _regler(at, "start_platz").disabled
    at.sidebar.button(key="preset_Hallenverbund 8×8").click().run()
    assert not _regler(at, "a").disabled and _regler(at, "groesse").disabled and _regler(at, "start_platz").disabled
    assert not _regler(at, "gamma").disabled
    at.sidebar.button(key="preset_Welche Größe?").click().run()
    assert _regler(at, "gamma").disabled
