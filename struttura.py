# Step 1: Creazione struttura base dei file per il gioco

from pathlib import Path

# Directory principale
base_dir = Path("DialoghiConUnEco")

# Sottocartelle
subdirs = [
    base_dir / "assets" / "audio",
    base_dir / "assets" / "fonts",
    base_dir / "scenes",
    base_dir / "engine"
]

# File da creare
files_to_create = {
    base_dir / "main.py": "# Punto di ingresso del gioco\n",
    base_dir / "README.md": "# Dialoghi con un'Eco - Gioco narrativo basato su poesia\n",
    base_dir / "engine" / "__init__.py": "",
    base_dir / "engine" / "dialog_manager.py": "# Gestione dei dialoghi\n",
    base_dir / "scenes" / "scene1.py": "# Scena 1: La stanza. Il crash.\n"
}

# Creazione delle cartelle
for folder in subdirs:
    folder.mkdir(parents=True, exist_ok=True)

# Creazione dei file vuoti con intestazione
for filepath, content in files_to_create.items():
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(content)

str(base_dir)
