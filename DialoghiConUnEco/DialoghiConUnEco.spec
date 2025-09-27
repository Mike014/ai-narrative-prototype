# DialoghiConUnEco.spec
# -*- mode: python ; coding: utf-8 -*-

import os
from PyInstaller.utils.hooks import collect_submodules
from PyInstaller.building.datastruct import Tree

SPEC_DIR = os.path.dirname(os.path.abspath(__file__)) if '__file__' in globals() else os.getcwd()
block_cipher = None

hiddenimports = []
hiddenimports += collect_submodules('pygame')
hiddenimports += collect_submodules('numpy')       # ← opzionale ma utile
hiddenimports += collect_submodules('requests')    # ← opzionale ma utile
hiddenimports += ['dotenv', 'plyer']

# datas di base
_datas = [
    ('Documenti_GD', 'Documenti_GD'),
    ('entita_metrics.csv', '.'),
    ('log_entita.txt', '.'),
    ('.env.game', '.'),
]

# includi .env.game se presente (NON la tua .env con chiavi vere!)
env_game = os.path.join(SPEC_DIR, '.env.game')
if os.path.exists(env_game):
    _datas.append((env_game, '.'))

a = Analysis(
    ['main.py'],
    pathex=[SPEC_DIR],
    binaries=[],
    datas=_datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=['tensorflow','tensorflow_intel','keras','tf_keras','torch'],
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    name='DialoghiConUnEco',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    debug=True,
    console=True,
    icon=os.path.join(SPEC_DIR, 'assets', 'background', 'logo.ico'),  # ← robusto
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    Tree(os.path.join(SPEC_DIR, 'assets'), prefix='assets'),
    Tree(os.path.join(SPEC_DIR, 'scenes'), prefix='scenes'),
    # Tree(os.path.join(SPEC_DIR, 'engine'), prefix='engine'),  # di solito NON serve al gioco
    strip=False,
    upx=True,
    upx_exclude=[],
    name='DialoghiConUnEco',
)
