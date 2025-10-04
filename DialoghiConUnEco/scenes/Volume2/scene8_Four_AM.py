# -*- coding: utf-8 -*-
# scenes/Volume2/scene8_Four_AM.py
import textwrap
import subprocess
from pathlib import Path
import pygame

from engine.engine_eleven_labs import ensure_cached_tts, VOICE_ID, DEFAULT_MODEL, OUT_FMT

# === OPZIONI SCENA ===========================================================
USE_AMBIENT = True       # True = musica ON (sotto), False = solo voce
USE_DUCKING = True          # se USE_AMBIENT True: abbassa musica mentre parla
AMBIENT_VOL = 0.25          # volume musica base
DUCKED_VOL  = 0.07          # volume musica mentre parla ENTITÀ
# ============================================================================

def find_root(start: Path) -> Path:
    p = start.resolve()
    for _ in range(6):
        if (p / "assets").exists() and (p / "engine").exists():
            return p
        p = p.parent
    return start

BASE_DIR = find_root(Path(__file__))
ASSETS   = BASE_DIR / "assets"
GEN_DIR  = ASSETS / "audio" / "generated"
GEN_DIR.mkdir(parents=True, exist_ok=True)

MONOLOGO = (
    "Ciao, io sono ENTITÀ… dimmi: come ti senti oggi? Fragile?\n"
    "Vorrei trascinarti nel buio del mare alle quattro.\n"
    "Quando tutti dormono, tu conti aerei che non prenderai mai.\n"
    "Ti hanno incatenata al mondo, vero? Sogni nelle bottiglie vuote.\n"
    "Speri che io le trovi. Ma io le rompo, non le apro. Ah… ahahaha… ahAHah."
)

MP3_FILE = GEN_DIR / "entita_four_am_scene8.mp3"
WAV_FILE = GEN_DIR / "entita_four_am_scene8.wav"   # fallback caricato da pygame

def wrap_text(text: str, width: int = 60):
    lines = []
    for para in text.split("\n"):
        lines += textwrap.wrap(para, width=width) or [""]
    return lines

def load_background(screen: pygame.Surface) -> pygame.Surface:
    for name in ("scena3_bg.png", "scena2_pic.png", "room.png", "menu.png", "what_am_I.png"):
        p = ASSETS / "background" / name
        if p.exists():
            img = pygame.image.load(str(p)).convert()
            return pygame.transform.scale(img, screen.get_size())
    surf = pygame.Surface(screen.get_size()); surf.fill((0, 0, 0))
    return surf

def ensure_audio_files():
    """Genera MP3 (se serve). Se MP3 non caricabile/è vuoto, transcodifica in WAV."""
    path = ensure_cached_tts(
        MONOLOGO, str(MP3_FILE),
        voice_id=VOICE_ID, model_id=DEFAULT_MODEL, output_format=OUT_FMT
    )
    if Path(path).stat().st_size < 1024:
        try: Path(path).unlink()
        except Exception: pass
        fallback_fmt = "mp3_44100_32"
        path = ensure_cached_tts(
            MONOLOGO, str(MP3_FILE),
            voice_id=VOICE_ID, model_id=DEFAULT_MODEL, output_format=fallback_fmt
        )
    # quick check: se pygame non lo digerisce → converto in WAV
    try:
        _ = pygame.mixer.Sound(path)
        return path
    except Exception:
        try:
            subprocess.run([
                "ffmpeg", "-y", "-loglevel", "error",
                "-i", str(MP3_FILE),
                "-ar", "44100", "-ac", "2", str(WAV_FILE)
            ], check=True)
            return str(WAV_FILE)
        except Exception as e:
            raise RuntimeError(f"Transcodifica WAV fallita: {e}")

def avvia_scena(screen: pygame.Surface, clock: pygame.time.Clock):
    """Entry point invocato dal tuo main.run_scene_module(screen, clock)."""
    # niente init/quit qui: usa ambiente già creato nel main
    bg = load_background(screen)

    # font
    font_path = ASSETS / "fonts" / "entity.ttf"
    font = pygame.font.Font(str(font_path), 28) if font_path.exists() else pygame.font.SysFont("consolas", 28)

    # musica ambiente opzionale (non blocca se manca)
    music_loaded = False
    if USE_AMBIENT:
        ambient = ASSETS / "audio" / "s3.wav"
        if ambient.exists():
            try:
                pygame.mixer.music.load(str(ambient))
                pygame.mixer.music.set_volume(AMBIENT_VOL if not USE_DUCKING else DUCKED_VOL)
                pygame.mixer.music.play(-1, fade_ms=800)
                music_loaded = True
            except Exception:
                music_loaded = False

    # audio ENTITÀ (robusto)
    try:
        playable_path = ensure_audio_files()
    except Exception as e:
        # mostra errore e rientra al menu
        screen.fill((0, 0, 0))
        msg = f"Errore TTS/Audio: {e}"
        err_font = pygame.font.SysFont(None, 24)
        surf = err_font.render(msg, True, (250, 80, 80))
        screen.blit(surf, surf.get_rect(center=(screen.get_width()//2, screen.get_height()//2)))
        pygame.display.flip()
        pygame.time.wait(2000)
        if music_loaded:
            try: pygame.mixer.music.fadeout(500)
            except Exception: pass
        return

    voice = pygame.mixer.Sound(playable_path)
    voice.set_volume(0.95)

    # ducking all’avvio voce
    if USE_AMBIENT and USE_DUCKING and music_loaded:
        try: pygame.mixer.music.set_volume(DUCKED_VOL)
        except Exception: pass

    channel = voice.play(fade_ms=200)

    # testo
    lines = wrap_text(MONOLOGO, width=64)
    color = (255, 60, 60)

    running = True
    while running:
        for e in pygame.event.get():
            if e.type == pygame.QUIT:
                return
            if e.type == pygame.KEYDOWN and e.key in (pygame.K_ESCAPE, pygame.K_RETURN):
                return

        screen.blit(bg, (0, 0))

        # sottotitoli centrati
        y = screen.get_height() // 2 - (len(lines) * 34) // 2
        for line in lines:
            surf = font.render(line, True, color)
            rect = surf.get_rect(center=(screen.get_width() // 2, y))
            screen.blit(surf, rect)
            y += 34

        # quando finisce la voce: risale la musica (se attiva) e mostra tip
        if not channel.get_busy():
            if USE_AMBIENT and music_loaded:
                try: pygame.mixer.music.set_volume(AMBIENT_VOL)
                except Exception: pass
            tip = pygame.font.SysFont(None, 22).render("Premi INVIO per continuare…", True, (220, 220, 220))
            screen.blit(tip, tip.get_rect(center=(screen.get_width() // 2, screen.get_height() - 50)))

        pygame.display.flip()
        clock.tick(60)
