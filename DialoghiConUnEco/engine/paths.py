# engine/paths.py
import sys
from pathlib import Path

def _find_base_dir(start: Path) -> Path:
    # In eseguibile PyInstaller
    if getattr(sys, "frozen", False):
        return Path(sys.executable).parent

    # Se è un file, sali di uno
    p = start.parent if start.is_file() else start

    # Risali finché trovi sia 'assets' che 'engine'
    for _ in range(10):
        if (p / "assets").exists() and (p / "engine").exists():
            return p
        p = p.parent

    # Fallback: working dir
    return Path.cwd()

THIS_FILE = Path(__file__).resolve()
BASE_DIR  = _find_base_dir(THIS_FILE)
ASSETS_DIR = BASE_DIR / "assets"

def base_path(*parts) -> str:
    return str(BASE_DIR.joinpath(*parts))

def asset_path(*parts) -> str:
    return str(ASSETS_DIR.joinpath(*parts))
