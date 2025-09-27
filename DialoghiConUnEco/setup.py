# setup.py
from cx_Freeze import setup, Executable
import sys, os

include_files = [
    ("assets", "assets"),
    ("engine", "engine"),
    ("scenes", "scenes"),
    ("Documenti_GD", "Documenti_GD"),
    (".env.game", ".env.game"),           # il tuo env per il gioco
    ("entita_metrics.csv", "entita_metrics.csv"),
    ("log_entita.txt", "log_entita.txt"),
]

build_exe_options = {
    "includes": ["dotenv", "plyer", "pygame", "requests"],
    # escludi roba pesante/optional (TensorFlow ecc.) per snellire
    "excludes": ["tensorflow", "keras", "numpy.f2py.tests", "pytest"],
    "include_files": include_files,
    "include_msvcr": True,  # runtime MSVC su Windows
}

base = "Win32GUI" if sys.platform == "win32" else None

setup(
    name="DialoghiConUnEco",
    version="0.1",
    options={"build_exe": build_exe_options},
    executables=[
        Executable(
            "main.py",
            base=base,
            icon=os.path.join("assets", "background", "logo.ico"),
            target_name="DialoghiConUnEco.exe",
        )
    ],
)
