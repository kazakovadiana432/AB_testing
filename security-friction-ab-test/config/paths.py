"""Filesystem paths"""

from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "data"
SRC_DIR = ROOT / "src"
DOCS_DIR = ROOT / "docs"
DATA_PATH = DATA_DIR / "recovery_ab.csv"