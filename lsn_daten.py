"""Die vorgerechneten Messungen (`daten/vorgerechnet.json`, erzeugt von `tools/vorrechnen.py`). Ohne Streamlit.

JSON kennt nur Textschlüssel: die Zellen (Gruppengrößen, Hallenseiten, Netzgrößen) werden beim Laden wieder zu Zahlen."""

import json
from pathlib import Path

PFAD = Path(__file__).resolve().parent / "daten" / "vorgerechnet.json"


def _zahlen(d: dict) -> dict:
    return {int(k): v for k, v in d.items()}


def laden(pfad: Path = PFAD) -> dict:
    d = json.loads(pfad.read_text(encoding="utf-8"))
    d["test"] = {f: _zahlen(z) for f, z in d["test"].items()}
    d["netze"] = {f: _zahlen(z) for f, z in d["netze"].items()}
    d["n_reihe"] = _zahlen(d["n_reihe"])
    d["verbund_reihe"] = _zahlen(d["verbund_reihe"])
    return d
