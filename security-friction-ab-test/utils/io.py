"""Load data and set up import paths for a non-installed project."""

import sys
from pathlib import Path

import pandas as pd


def ensure_project_on_path():
    """Add project root + src/ so `config`, `utils`, and analysis modules import cleanly."""
    root = Path(__file__).resolve().parent.parent
    src = root / "src"
    for p in (root, src):
        s = str(p)
        if s not in sys.path:
            sys.path.insert(0, s)
    return root

def load_recovery_data(path=None):
    from config.paths import DATA_PATH

    path = path or DATA_PATH
    return pd.read_csv(path, parse_dates=["date"])