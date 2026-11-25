"""Permalink (Begrenzen), Presets (Schnellstart in der Seitenleiste, aktives Preset hervorgehoben) und Zufalls-Seed-Button (Standardmuster aus dem Demo-Portfolio).

Jeder Regler der Seitenleiste hat einen Eintrag in SETTING_SPECS. Werte aus der Adresszeile werden begrenzt (Zahlen) oder verworfen (unbekannte Auswahl).
Regler, die für die gewählte Netzfamilie nichts bewirken, werden ausgegraut (nicht ausgeblendet): ihr Wert bleibt erhalten."""

import random
from dataclasses import dataclass

import streamlit as st

import lsn_constants as C


@dataclass(frozen=True)
class SettingSpec:
    url_param: str
    caster: type
    default: object
    lo: float | None = None
    hi: float | None = None
    options: tuple | None = None      # erlaubte Werte (Auswahllisten und Stufen)


_STANDARD = C.PRESETS[next(iter(C.PRESETS))]


def _spec(url, caster, name, lo=None, hi=None, options=None):
    return SettingSpec(url, caster, _STANDARD[name], lo, hi, options)


SETTING_SPECS = {
    "netz": _spec("netz", str, "netz", options=C.NETZE),
    "a": _spec("a", int, "a", options=C.A_STUFEN),
    "z": _spec("z", int, "z", options=C.Z_STUFEN),
    "groesse": _spec("g", int, "groesse", options=C.GROESSE_STUFEN),
    "aussen": _spec("aussen", int, "aussen", options=C.AUSSEN_STUFEN),
    "n": _spec("n", int, "n", options=C.N_STUFEN),
    "sammelart": _spec("sammel", str, "sammelart", options=C.SAMMEL_ARTEN_APP),
    "start_platz": _spec("start", int, "start_platz", options=tuple(range(6))),
    "start_halle": _spec("hstart", str, "start_halle", options=C.HALLEN_STARTS),
    "verfahren": _spec("verfahren", str, "verfahren", options=C.VERFAHREN_APP),
    "beta": _spec("beta", float, "beta", options=C.BETA_STUFEN),
    "eps": _spec("eps", float, "eps", options=C.EPS_STUFEN),
    "regel": _spec("regel", str, "regel", options=C.REGELN),
    "gamma": _spec("gamma", float, "gamma", options=C.GAMMA_STUFEN),
    "gierig_art": _spec("gierig", str, "gierig_art", options=tuple(C.GIERIG_TEXT)),
    "budget": _spec("budget", int, "budget", options=C.BUDGET_STUFEN),
    "seed": _spec("seed", int, "seed", 0, C.SEED_MAX),
}
PRESET_KEYS = {key: key for key in SETTING_SPECS}


def init_session_state_defaults():
    for state_key, spec in SETTING_SPECS.items():
        if state_key not in st.session_state:
            st.session_state[state_key] = spec.default


def bounds(state_key):
    spec = SETTING_SPECS[state_key]
    return spec.lo, spec.hi


def _eingerastet(spec: SettingSpec, wert):
    """Zahlen auf die Grenzen begrenzt; unbekannte Auswahl gibt None. Fließkomma-Stufen werden mit kleiner Toleranz erkannt."""
    if spec.options is not None:
        if spec.caster is float:
            return next((o for o in spec.options if abs(o - wert) <= 1e-9 * max(abs(o), 1.0)), None)
        return wert if wert in spec.options else None
    if spec.lo is not None:
        wert = max(spec.lo, wert)
    if spec.hi is not None:
        wert = min(spec.hi, wert)
    return wert


def load_permalink_settings():
    """Einmal je Sitzung: Werte aus der Adresszeile übernehmen."""
    if "permalink_loaded" in st.session_state:
        return
    qp = st.query_params
    for state_key, spec in SETTING_SPECS.items():
        if spec.url_param in qp:
            try:
                wert = _eingerastet(spec, spec.caster(qp[spec.url_param]))
            except (ValueError, TypeError, OverflowError):
                continue
            if wert is not None:
                st.session_state[state_key] = wert
    st.session_state["permalink_loaded"] = True


def sync_query_params(values):
    """`values`: {state_key: aktueller Wert}; die Adresszeile spiegelt die Konfiguration."""
    try:
        for state_key, value in values.items():
            st.query_params[SETTING_SPECS[state_key].url_param] = str(value)
    except Exception:
        pass


def apply_preset(name):
    for key, state_key in PRESET_KEYS.items():
        if key in C.PRESETS[name]:
            st.session_state[state_key] = C.PRESETS[name][key]


def aktives_preset():
    """Name des Presets, dessen Werte GENAU den aktuellen Einstellungen entsprechen, sonst None (verglichen wird jeder Regler aus SETTING_SPECS)."""
    preset_key_of = {state_key: key for key, state_key in PRESET_KEYS.items()}
    for name, preset in C.PRESETS.items():
        if all(
            st.session_state.get(state_key, spec.default) == preset.get(preset_key_of.get(state_key), spec.default)
            for state_key, spec in SETTING_SPECS.items()
        ):
            return name
    return None


def sidebar_presets():
    """Schnellstart oben in der Seitenleiste; das aktive Preset ist hervorgehoben (`type="primary"`)."""
    st.header("🎯 Schnellstart")
    st.caption("Ein Beispielszenario laden:")
    aktiv = aktives_preset()
    for name in C.PRESETS:
        st.button(
            name, width="stretch", on_click=apply_preset, args=(name,), help=C.PRESET_HELP.get(name, ""), key=f"preset_{name}",
            type="primary" if aktiv == name else "secondary",
        )


def randomize_seed():
    st.session_state["seed"] = random.randint(0, C.SEED_MAX)
