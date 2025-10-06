# -*- coding: utf-8 -*-
"""
EstablishEnvironment (Python) — Rilevatore dell'ambiente di runtime per giochi Pygame.

- Rileva OS, versione SDL, backend video
- Legge la risoluzione del desktop (senza creare finestre visibili)
- Stima il fattore di scala DPI su Windows
- Classifica il device: DESKTOP, TABLET, MINI_TABLET, PHONE
- Riconosce eseguibili "frozen" (PyInstaller)
- Fornisce stringa descrittiva e JSON
- Suggerisce una size finestra sicura rispetto al desktop

È sicuro importarlo prima di chiamare pygame.display.set_mode().
"""
from __future__ import annotations

import os
import sys
import json
import platform
from dataclasses import dataclass, asdict
from enum import Enum
from typing import Tuple

try:
    import pygame  # type: ignore
except Exception:
    pygame = None  # Consentire import anche in ambienti senza pygame (CI, toolchain)

# -----------------------------
# Tipologia di dispositivo
# -----------------------------
class DeviceType(Enum):
    DESKTOP = 1
    TABLET = 2
    MINI_TABLET = 3
    PHONE = 4

@dataclass
class Environment:
    operating_system: str = ""
    is_plugin: bool = False
    is_mobile_device: bool = False
    screen_width: int = 0
    screen_height: int = 0
    scale_factor: float = 1.0
    device_type: DeviceType = DeviceType.DESKTOP
    is_frozen: bool = False
    sdl_version: Tuple[int, int, int] = (0, 0, 0)
    windowing_backend: str = ""

class _EstablishEnvironment:
    """Singleton stile JUCE, ma in Python: usa env = _EstablishEnvironment() in fondo al file."""
    def __init__(self) -> None:
        self._env: Environment = Environment()
        self._initialized: bool = False

    # ---------------- Public API ----------------
    def init(self, allow_temp_display: bool = True) -> None:
        """
        Inizializza le informazioni d'ambiente (idempotente).
        """
        if self._initialized:
            return

        e = Environment()
        e.is_frozen = bool(getattr(sys, "frozen", False))

        # OS
        e.operating_system = self._detect_os_string()

        # "Plugin" non ha un corrispettivo in pygame; lasciamo False per parità con il design JUCE.
        e.is_plugin = False

        # SDL/back-end
        if pygame is not None:
            try:
                e.sdl_version = pygame.get_sdl_version()
            except Exception:
                e.sdl_version = (0, 0, 0)
            e.windowing_backend = os.environ.get("SDL_VIDEODRIVER", "") or ""

        # Mobile (per porting futuri)
        e.is_mobile_device = self._is_mobile_platform()

        # Dimensioni schermo + Scala DPI
        e.screen_width, e.screen_height = self._detect_screen_size(allow_temp_display=allow_temp_display)
        e.scale_factor = self._detect_scale_factor(default=1.0)

        # Classificazione device
        e.device_type = self._classify_device(e)

        self._env = e
        self._initialized = True

    def get(self) -> Environment:
        """Restituisce il dataclass Environment; chiama init() se non già inizializzato."""
        if not self._initialized:
            self.init()
        return self._env

    def get_device_description(self) -> str:
        """Stringa human-readable, utile per log/overlay."""
        e = self.get()
        mode = "Mobile" if e.is_mobile_device else "Desktop"
        plugin = "Yes" if e.is_plugin else "No"
        return (
            f"{e.operating_system} | {mode} | "
            f"{e.screen_width}x{e.screen_height} (scale {self._fmt_scale(e.scale_factor)}) | "
            f"Plugin: {plugin} | Device Type: {e.device_type.name}"
        )

    def to_json(self, pretty: bool = True) -> str:
        """Dump JSON (device_type come stringa)."""
        e = self.get()
        payload = asdict(e)
        payload["device_type"] = e.device_type.name
        return json.dumps(payload, indent=2 if pretty else None, ensure_ascii=False)

    def suggest_window_size(self, preferred: Tuple[int, int], margin: int = 0) -> Tuple[int, int]:
        """
        Clampa una size preferita ai limiti del desktop meno un margine.
        Ritorna una size che non eccede la risoluzione rilevata.
        """
        e = self.get()
        W, H = e.screen_width, e.screen_height
        w, h = preferred
        w = min(max(320, w), max(320, W - margin))
        h = min(max(240, h), max(240, H - margin))
        return (w, h)

    # ---------------- Internals -----------------
    def _detect_os_string(self) -> str:
        try:
            sysname = platform.system() or sys.platform
            release = platform.release() or ""
            if sysname and release:
                return f"{sysname} {release}".strip()
            return sysname or "Unknown OS"
        except Exception:
            return "Unknown OS"

    def _is_mobile_platform(self) -> bool:
        sp = (sys.platform or "").lower()
        if any(k in sp for k in ("ios", "android", "emscripten")):
            return True
        if os.environ.get("KIVY_BUILD") or os.environ.get("ANDROID_ARGUMENT"):
            return True
        return False

    def _detect_screen_size(self, allow_temp_display: bool) -> Tuple[int, int]:
        if pygame is not None:
            try:
                if not pygame.get_init():
                    pygame.init()
                if not pygame.display.get_init():
                    pygame.display.init()

                if hasattr(pygame.display, "get_desktop_sizes"):
                    sizes = pygame.display.get_desktop_sizes()
                    if sizes and len(sizes[0]) == 2:
                        return sizes[0][0], sizes[0][1]
            except Exception:
                pass

            # Fallback: finestra nascosta temporanea per leggere Info
            if allow_temp_display:
                try:
                    flags = 0
                    if hasattr(pygame, "HIDDEN"):
                        flags |= pygame.HIDDEN  # type: ignore[attr-defined]
                    pygame.display.set_mode((1, 1), flags)
                    info = pygame.display.Info()  # type: ignore
                    w, h = int(getattr(info, "current_w", 0)), int(getattr(info, "current_h", 0))
                    pygame.display.quit()
                    return (w or 1280, h or 720)
                except Exception:
                    try:
                        pygame.display.quit()
                    except Exception:
                        pass

        # Ultima spiaggia
        return (1280, 720)

    def _detect_scale_factor(self, default: float = 1.0) -> float:
        if sys.platform.startswith("win"):
            try:
                import ctypes
                try:
                    user32 = ctypes.windll.user32
                    user32.SetProcessDPIAware()
                    dpi = user32.GetDpiForSystem()
                    if dpi:
                        return max(0.5, min(4.0, float(dpi) / 96.0))
                except Exception:
                    pass
                try:
                    shcore = ctypes.windll.shcore
                    scale = ctypes.c_int()
                    hr = shcore.GetScaleFactorForDevice(0, ctypes.byref(scale))
                    if hr == 0 and scale.value:
                        return max(0.5, min(4.0, float(scale.value) / 100.0))
                except Exception:
                    pass
                try:
                    user32 = ctypes.windll.user32
                    dc = user32.GetDC(0)
                    LOGPIXELSX = 88
                    gdi = ctypes.windll.gdi32
                    dpi = gdi.GetDeviceCaps(dc, LOGPIXELSX)
                    user32.ReleaseDC(0, dc)
                    if dpi:
                        return max(0.5, min(4.0, float(dpi) / 96.0))
                except Exception:
                    pass
            except Exception:
                return default
        return default

    def _classify_device(self, e: Environment) -> DeviceType:
        if e.is_mobile_device:
            w, h = max(e.screen_width, e.screen_height), min(e.screen_width, e.screen_height)
            if w >= 1280 and h >= 800:
                return DeviceType.TABLET
            elif w >= 720:
                return DeviceType.MINI_TABLET
            else:
                return DeviceType.PHONE
        return DeviceType.DESKTOP

    @staticmethod
    def _fmt_scale(x: float) -> str:
        return f"{x:.2f}".rstrip("0").rstrip(".")

# Istanza singleton
env = _EstablishEnvironment()

if __name__ == "__main__":
    env.init()
    print(env.get_device_description())
    print(env.to_json(pretty=True))

