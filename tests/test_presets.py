"""Presets und Permalink: Vollständigkeit, gültige Werte, Standard-Preset = Standardeinstellungen, Einrasten und Verwerfen."""

import dataclasses

import lsn_constants as C
import lsn_evaluation as E
import lsn_presets as P


def test_every_preset_has_help_and_all_keys():
    assert set(C.PRESETS) == set(C.PRESET_HELP)
    for name, preset in C.PRESETS.items():
        assert set(preset) == set(P.PRESET_KEYS), name
        assert C.PRESET_HELP[name]


def test_preset_values_are_allowed():
    for name, preset in C.PRESETS.items():
        for key, wert in preset.items():
            spec = P.SETTING_SPECS[key]
            assert P._eingerastet(spec, wert) == wert, (name, key)


def test_setting_specs_cover_exactly_the_settings():
    assert set(P.SETTING_SPECS) == {f.name for f in dataclasses.fields(E.Settings)}


def test_default_preset_equals_the_default_settings():
    erstes = C.PRESETS[next(iter(C.PRESETS))]
    assert all(P.SETTING_SPECS[k].default == erstes[k] for k in P.SETTING_SPECS)


def test_presets_are_pairwise_different():
    werte = [tuple(sorted(p.items())) for p in C.PRESETS.values()]
    assert len(set(werte)) == len(werte)


def test_welche_groesse_differs_from_hallenverbund_only_in_the_rule():
    a, b = C.PRESETS["Hallenverbund 8×8"], C.PRESETS["Welche Größe?"]
    assert {k for k in a if a[k] != b[k]} == {"regel"}


def test_eingerastet_begrenzt_zahlen_und_verwirft_unbekannte_auswahl():
    seed = P.SETTING_SPECS["seed"]
    assert P._eingerastet(seed, -5) == 0 and P._eingerastet(seed, 10 ** 9) == C.SEED_MAX
    assert P._eingerastet(P.SETTING_SPECS["netz"], "nichts") is None
    assert P._eingerastet(P.SETTING_SPECS["beta"], 0.1 + 1e-15) == 0.1
    assert P._eingerastet(P.SETTING_SPECS["beta"], 0.11) is None
    assert P._eingerastet(P.SETTING_SPECS["a"], 7) is None


def test_bounds_of_numbers():
    assert P.bounds("seed") == (0, C.SEED_MAX)
