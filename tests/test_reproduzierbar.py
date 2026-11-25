"""Gleicher Zufalls-Seed gibt in zwei Prozessen mit verschiedener Hash-Randomisierung dasselbe Netz und dieselben Schnitte."""

import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

SKRIPT = ROOT / "tests" / "reproduzierbar_lauf.py"


def _lauf(hashseed: str) -> str:
    env = dict(os.environ, PYTHONHASHSEED=hashseed, PYTHONIOENCODING="utf-8")
    return subprocess.run([sys.executable, "-B", str(SKRIPT)], capture_output=True, text=True, check=True, env=env, timeout=120, stdin=subprocess.DEVNULL).stdout


def test_zwei_hash_seeds_dasselbe_ergebnis():
    a, b = _lauf("1"), _lauf("2")
    assert a == b and a.count("\n") >= 8
