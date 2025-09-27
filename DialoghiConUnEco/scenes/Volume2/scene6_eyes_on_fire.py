# scenes/Volume1/scene_lui_eyes_on_fire_sync145_dropstart.py
# -*- coding: utf-8 -*-

import sys, os, random
from pathlib import Path
from typing import List, Tuple, Optional

import numpy as np
import pygame
from dotenv import load_dotenv

load_dotenv()

# ------------------------------- Project root --------------------------------
def find_project_root(start: Path) -> Path:
    p = start
    for _ in range(6):
        if (p / "assets").exists() and (p / "engine").exists():
            return p
        p = p.parent
    return start

THIS_FILE  = Path(__file__).resolve()
BASE_DIR   = find_project_root(THIS_FILE)
ASSETS_DIR = BASE_DIR / "assets"

def asset_path(*parts) -> str:
    return str(ASSETS_DIR.joinpath(*parts))

# --------------------------------- Visual ------------------------------------
WIDTH, HEIGHT = 1280, 720
FPS = 60
FONT_SIZE = 48
TEXT_COLOR = (245, 245, 250)
BG_COLOR = (0, 0, 0)

# --- Logo intro (pre-drop) ---
LOGO_PATH = asset_path("background", "logo.jpg")
LOGO_FADE_IN_SEC = 24.4          # durata fade-in logo
GLITCH_ONLY_DURING_FADE = True    # glitch solo durante il fade

# ------------------------------- Synchronization ------------------------------
# BPM 145 → 1 beat = 60/145 s
BPM = 145.0
BEAT_SEC = 60.0 / BPM          # ~0.4137931034 s
BEATS_PER_SEC = 1.0 / BEAT_SEC

# Vincoli cronometrici
ALIGN_DROP_SEC    = 26.000     # Bar 1 • Beat 1
REF_END_LUI_SEC   = 52.960
REF_END_IOCOS_SEC = 79.440
TRACK_END_SEC     = 92.500

# Conversioni in beat (continui, non arrotondare)
PRE_ROLL_BEATS = ALIGN_DROP_SEC    * BEATS_PER_SEC    # ~62.8333
LUI_BEATS      = (REF_END_LUI_SEC   - ALIGN_DROP_SEC) * BEATS_PER_SEC    # ~65.1533
IOCOS_BEATS    = (REF_END_IOCOS_SEC - REF_END_LUI_SEC)* BEATS_PER_SEC    # ~63.9933
ENTITA_BEATS   = (TRACK_END_SEC     - REF_END_IOCOS_SEC)*BEATS_PER_SEC   # ~31.5617

# Offset micro (regolabile live)
OFFSET_SEC = -0.29  # in secondi, positivo = anticipa, negativo = ritarda
OFFSET_STEP_SMALL = 0.010
OFFSET_STEP_LARGE = 0.050

# HUD / Grid
SHOW_GRID = True
SHOW_HUD  = True
VERBOSE_HIT_LOG = True

# ------------------------------- Timeline builder -----------------------------
def _build_timeline() -> List[Tuple[float, str]]:
    """
    Ogni entry è (durata_in_beats, testo).
    Prima del drop: NESSUNA battuta (schermo vuoto).
    Dal drop (0:26.000): parte LUI e segue tutta la metrica richiesta.
    """
    tl: List[Tuple[float, str]] = []

    # --- PRE-ROLL (fino al drop): schermo vuoto, nessuna battuta ---
    tl.append((PRE_ROLL_BEATS, ""))

    # --- LUI (dal drop fino a 52.960) ---
    # 10 battute: 9 blocchi da 6 beat + 1 blocco remainder per centrare il target
    base = 6.0
    n_fixed = 9
    remainder = max(0.0, LUI_BEATS - base * n_fixed)  # ~11.1533 beats
    lui_blocks = [base]*n_fixed + [remainder]
    lui_texts = [
        "LUI: Mattina. Mi alzo.",
        "LUI: Trigger fisso. Fiore rosa sul tavolo.",
        "LUI: Occhi che bruciano. Secchi.",
        "LUI: Vado piano. Le nutro, le fiamme.",
        "LUI: Parlano loro, alla fine. Dicono chi sei.",
        "LUI: Il pensiero di te non regge.",
        "LUI: Scorticato vivo nel cervello.",
        "LUI: Ti amo.",
        "LUI: Ma ti cerco solo nei corridoi della testa. Anticamere.",
        "LUI: Ricordo chi sei. Non mi salva niente.\nNon lenirò il tuo dolore. Attraversalo.\nCome ho fatto io.\nFinché quel dolore non butta giù tutto il resto. Tutti i nemici.",
    ]
    for beats, text in zip(lui_blocks, lui_texts):
        tl.append((beats, text))

    # --- IO ↔ COSCIENZA (fino a 79.440) ---
    # 3 blocchi: 14 + 16 + remainder ≈ 33.9933 beat
    io_a = 14.0
    io_b = 16.0
    io_remainder = max(0.0, IOCOS_BEATS - (io_a + io_b))
    tl += [
        (io_a,        "IO: È un loop... ma la radio si è rotta."),
        (io_b,        "IO: Chi siamo ora?"),
        (io_remainder,"COSCIENZA: Siamo ciò che resta quando l’eco tace."),
    ]

    # --- ENTITÀ (OS) fino a fine brano ---
    tl.append((ENTITA_BEATS, "[NOTIFICA OS] Processo interrotto. Nessun salvataggio disponibile."))

    return tl

TIMELINE_BEATS: List[Tuple[float, str]] = _build_timeline()

# ------------------------------- Debug helpers --------------------------------
def fmt_time(sec: float) -> str:
    if sec < 0: sec = 0.0
    m = int(sec // 60)
    s = int(sec % 60)
    ms = int(round((sec - int(sec)) * 1000.0))
    return f"{m}:{s:02d}.{ms:03d}"

def cumulative_change_beats(timeline_beats):
    beats = []
    acc = 0.0
    for b, _ in timeline_beats:
        acc += b
        beats.append(acc)
    return beats

def print_timeline_table(change_beats, timeline_beats):
    print("\n================= TIMELINE DEBUG (145 BPM) =================")
    print(f"BPM={BPM:.3f}  BEAT_SEC={BEAT_SEC:.9f}s  BEATS/s={BEATS_PER_SEC:.6f}")
    print(f"DROP        @ {fmt_time(ALIGN_DROP_SEC)}  (PRE_ROLL_BEATS={PRE_ROLL_BEATS:.6f})")
    print(f"END LUI     @ {fmt_time(REF_END_LUI_SEC)}   (LUI_BEATS={LUI_BEATS:.6f})")
    print(f"END IO/C    @ {fmt_time(REF_END_IOCOS_SEC)} (IOCOS_BEATS={IOCOS_BEATS:.6f})")
    print(f"END TRACK   @ {fmt_time(TRACK_END_SEC)}     (ENTITA_BEATS={ENTITA_BEATS:.6f})\n")

    acc_prev = 0.0
    for i, ((dur_b, text), acc_b) in enumerate(zip(timeline_beats, change_beats)):
        start_sec = acc_prev * BEAT_SEC
        end_sec   = acc_b   * BEAT_SEC
        who = (text.split(":")[0] if ":" in text else "").strip()
        print(f"[{i:02d}] {who:10s} | dur={dur_b:8.3f} beats ({dur_b*BEAT_SEC:6.3f}s) | "
              f"{fmt_time(start_sec)} → {fmt_time(end_sec)} | '{text[:48]}'")
        acc_prev = acc_b

    total_beats = change_beats[-1]
    total_sec = total_beats * BEAT_SEC
    # indici di controllo
    last_lui_idx = max(i for i, (_, t) in enumerate(timeline_beats) if t.startswith("LUI:"))
    end_lui_sec = change_beats[last_lui_idx] * BEAT_SEC
    end_iocos_idx = len(timeline_beats) - 2
    end_iocos_sec = change_beats[end_iocos_idx] * BEAT_SEC

    print("\n----------------- RIEPILOGO -----------------")
    print(f"Totale timeline: {total_beats:.3f} beats → {fmt_time(total_sec)} "
          f"(Δfine={total_sec-TRACK_END_SEC:+.3f}s)")
    print(f"End LUI  calc {fmt_time(end_lui_sec)}  vs target {fmt_time(REF_END_LUI_SEC)} "
          f"(Δ={end_lui_sec-REF_END_LUI_SEC:+.3f}s)")
    print(f"End IO/C calc {fmt_time(end_iocos_sec)} vs target {fmt_time(REF_END_IOCOS_SEC)} "
          f"(Δ={end_iocos_sec-REF_END_IOCOS_SEC:+.3f}s)")
    print("============================================================\n")

# ------------------------------- Glitch safe ----------------------------------
def apply_glitch(surface: pygame.Surface) -> pygame.Surface:
    w, h = surface.get_width(), surface.get_height()
    if w < 4 or h < 4: return surface
    arr = pygame.surfarray.array3d(surface)
    dx, dy = random.randint(-5, 5), random.randint(-5, 5)
    r = np.roll(arr[:, :, 0], dx, axis=0)
    g = np.roll(arr[:, :, 1], dy, axis=1)
    b = arr[:, :, 2]
    out = np.stack([r, g, b], axis=2)
    if h > 12:
        bands = random.randint(1, 3)
        for _ in range(bands):
            band_h = random.randint(2, min(10, h))
            y0 = random.randint(0, max(0, h - band_h))
            shift = random.randint(-20, 20)
            out[:, y0:y0 + band_h, :] = np.roll(out[:, y0:y0 + band_h, :], shift, axis=0)
    glitched = pygame.surfarray.make_surface(out)
    return glitched.convert_alpha()

# ----------------------------- Logo helpers (NEW) -----------------------------
def _load_and_scale_logo(path: str, w: int, h: int) -> Tuple[Optional[pygame.Surface], Optional[pygame.Rect]]:
    if not os.path.exists(path):
        print(f"[WARN] Logo non trovato: {path}")
        return None, None
    try:
        img = pygame.image.load(path).convert_alpha()
    except Exception as e:
        print(f"[WARN] Logo non caricato: {e}")
        return None, None
    iw, ih = img.get_size()
    scale = min(w / iw, h / ih) * 0.9   # “contain” con margine 10%
    new_size = (max(1, int(iw * scale)), max(1, int(ih * scale)))
    img = pygame.transform.smoothscale(img, new_size)
    rect = img.get_rect(center=(w // 2, h // 2))
    return img, rect

def _pixelate(surface: pygame.Surface, factor: float) -> pygame.Surface:
    """factor in (0,1] → risoluzione ridotta poi rialzata (effetto blocchi)."""
    factor = max(0.01, min(1.0, factor))
    if factor >= 0.995:
        return surface.copy()
    w, h = surface.get_size()
    small = pygame.transform.smoothscale(surface, (max(1, int(w * factor)), max(1, int(h * factor))))
    return pygame.transform.scale(small, (w, h))

def glitch_logo_frame(logo: pygame.Surface, progress: float) -> pygame.Surface:
    """
    progress 0..1: 0 = inizio fade (glitch forte), 1 = fine fade (glitch lieve/zero).
    - Pixelazione decrescente col tempo.
    - Sporadico channel/band shift riusando apply_glitch().
    """
    # pixelazione: a inizio fade riduci tanto (0.30), poi sali verso 1.0
    min_factor = 0.30 + 0.70 * progress         # 0.30 → 1.00
    max_factor = min(1.0, min_factor + 0.10)    # micro jitter
    factor = random.uniform(min_factor, max_factor)
    frame = _pixelate(logo, factor)

    # “rumore” (canali/bande) più probabile a inizio fade
    p = 0.60 * (1.0 - progress) + 0.10          # 0.70 → 0.10
    if random.random() < p:
        frame = apply_glitch(frame)

    return frame

# ------------------------------- Fonts/render ---------------------------------
io_font_path   = ASSETS_DIR / "fonts" / "fragile.ttf"
cosc_font_path = ASSETS_DIR / "fonts" / "reflective.ttf"

def make_font(size=FONT_SIZE, bold=False, who: str = "") -> pygame.font.Font:
    # IO → fragile.ttf
    if who.startswith("IO") and io_font_path.exists():
        return pygame.font.Font(str(io_font_path), size)
    # COSCIENZA → reflective.ttf
    if who.startswith("COSCIENZA") and cosc_font_path.exists():
        return pygame.font.Font(str(cosc_font_path), size)
    # fallback generico
    try: 
        return pygame.font.SysFont("DejaVu Sans", size, bold=bold)
    except Exception:
        try: 
            return pygame.font.SysFont("Arial", size, bold=bold)
        except Exception: 
            return pygame.font.Font(None, size)

def render_text_center(text: str, color, w: int, h: int):
    who = (text.split(":")[0] if ":" in text else "").strip()
    font = make_font(FONT_SIZE, bold=False, who=who)

    # --- wrapping su larghezza max (90% della finestra) ---
    max_width = int(w * 0.90)

    def _wrap_paragraph(para: str) -> list[str]:
        if not para:
            return [""]  # preserva righe vuote
        words = para.split(" ")
        lines, current = [], ""
        for word in words:
            candidate = (current + " " + word) if current else word
            if font.size(candidate)[0] <= max_width:
                current = candidate
            else:
                if current:
                    lines.append(current)
                    current = word
                else:
                    # parola singola più larga di max_width → spezza "hard"
                    chunk = ""
                    for ch in word:
                        c2 = chunk + ch
                        if font.size(c2)[0] <= max_width:
                            chunk = c2
                        else:
                            if chunk:
                                lines.append(chunk)
                            chunk = ch
                    current = chunk
        if current:
            lines.append(current)
        return lines

    # Supporta newline manuali: wrappa ogni paragrafo
    paragraphs = text.split("\n") if "\n" in text else [text]
    lines: list[str] = []
    for p in paragraphs:
        lines.extend(_wrap_paragraph(p))

    # Se tutto vuoto, rendi uno spazio (come prima)
    if not any(lines):
        surf = font.render(" ", True, color)
        rect = surf.get_rect(center=(w // 2, h // 2))
        return surf, rect

    # Render multiline centrato
    line_surfs = [font.render(ln if ln else " ", True, color) for ln in lines]
    spacing = int(font.get_linesize() * 0.12)
    total_h = sum(s.get_height() for s in line_surfs) + spacing * (len(line_surfs) - 1)
    canvas = pygame.Surface((w, total_h), pygame.SRCALPHA)
    y = 0
    for ls in line_surfs:
        x = (w - ls.get_width()) // 2
        canvas.blit(ls, (x, y))
        y += ls.get_height() + spacing
    rect = canvas.get_rect(center=(w // 2, h // 2))
    return canvas, rect

# ------------------------------- Grid / HUD -----------------------------------
def draw_grid(screen: pygame.Surface, current_beats: float, w: int, h: int):
    beat_num = int(current_beats)
    phase = current_beats - beat_num
    alpha = int(120 * (1.0 - phase) ** 2)
    bar = pygame.Surface((w, 2), pygame.SRCALPHA)
    bar.fill((255, 255, 255, max(0, min(120, alpha))))
    screen.blit(bar, (0, h - 10))
    # Flash a ogni Beat 1..4, dal drop in poi
    since_drop = current_beats - PRE_ROLL_BEATS
    if since_drop >= 0:
        beat_in_bar = since_drop % 4.0
        if beat_in_bar < 0.12:
            ring = pygame.Surface((w, h), pygame.SRCALPHA)
            ring.fill((255, 255, 255, 12))
            screen.blit(ring, (0, 0), special_flags=pygame.BLEND_ADD)

def draw_hud(screen, font_small, music_time, current_beats):
    since_drop_beats = current_beats - PRE_ROLL_BEATS
    if since_drop_beats >= 0:
        bar_idx = int(since_drop_beats // 4) + 1
        beat_in_bar = (since_drop_beats % 4.0) + 1.0
    else:
        bar_idx, beat_in_bar = 0, 0.0
    lines = [
        f"t={fmt_time(music_time)} | beats={current_beats:8.3f} | since_drop={max(0.0,since_drop_beats):8.3f}",
        f"bar={bar_idx} | beat_in_bar={beat_in_bar:4.2f} | OFFSET={int(OFFSET_SEC*1000):+d} ms",
        "Keys: [ / ] offset 10ms (Shift=50ms) | G grid | H HUD",
    ]
    y = 10
    for s in lines:
        hud = font_small.render(s, True, (180, 190, 205))
        screen.blit(hud, (10, y)); y += 20

# ------------------------------- Scene runner ---------------------------------
def run_intro(screen: pygame.Surface | None = None, clock: pygame.time.Clock | None = None):
    global OFFSET_SEC, SHOW_GRID, SHOW_HUD, WIDTH, HEIGHT
    print(f"[DEBUG][LUI] BASE_DIR:  {BASE_DIR}")
    print(f"[DEBUG][LUI] ASSETS_DIR:{ASSETS_DIR}")

    pygame.mixer.pre_init(44100, -16, 2, 256)  # buffer ridotto → meno latenza
    we_created_screen = False
    if screen is None or clock is None:
        pygame.init()
        pygame.mixer.init()
        screen = pygame.display.set_mode((WIDTH, HEIGHT))
        pygame.display.set_caption("LUI — Eyes on Fire (Skeler) — 145 BPM — DROP START")
        clock = pygame.time.Clock()
        we_created_screen = True
    else:
        WIDTH, HEIGHT = screen.get_size()

    font = make_font(FONT_SIZE, bold=False)
    font_small = make_font(18, bold=False)

    # Pre-render testo
    pre_surfs = []
    for _, text in TIMELINE_BEATS:
        surf, rect = render_text_center(text, TEXT_COLOR, WIDTH, HEIGHT)
        pre_surfs.append((surf, rect))

    change_beats = cumulative_change_beats(TIMELINE_BEATS)
    print_timeline_table(change_beats, TIMELINE_BEATS)

    # Audio
    audio_candidates = [
        asset_path("audio", "eyes_on_fire.ogg"),
        asset_path("audio", "eyes_on_fire.mp3"),
        asset_path("audio", "eyes_on_fire.wav"),
        asset_path("audio", "what_am_I_song.wav"),
        asset_path("audio", "what_am_I.wav"),
    ]
    music_started = False
    for ap in audio_candidates:
        if os.path.exists(ap):
            try:
                pygame.mixer.music.load(ap)
                pygame.mixer.music.play()
                music_started = True
                print(f"[DEBUG][LUI] Audio: {ap}")
                break
            except Exception as e:
                print("[LUI] Audio non caricato:", ap, e)

    # Carica logo
    logo_surf, logo_rect = _load_and_scale_logo(LOGO_PATH, WIDTH, HEIGHT)

    music_t0_ms = None  # calibra lo zero dell'audio
    block_idx = 0
    last_logged_idx = -1
    running = True

    while running:
        _dt = clock.tick(FPS) / 1000.0
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
                if we_created_screen:
                    pygame.mixer.music.stop(); pygame.quit(); sys.exit(0)
            if event.type == pygame.KEYDOWN:
                if event.key in (pygame.K_ESCAPE, pygame.K_RETURN, pygame.K_SPACE):
                    running = False
                if event.key == pygame.K_g:
                    SHOW_GRID = not SHOW_GRID; print(f"[DEBUG] SHOW_GRID = {SHOW_GRID}")
                if event.key == pygame.K_h:
                    SHOW_HUD  = not SHOW_HUD;  print(f"[DEBUG] SHOW_HUD  = {SHOW_HUD}")
                if event.key == pygame.K_RIGHTBRACKET:   # ]
                    OFFSET_SEC += (OFFSET_STEP_LARGE if pygame.key.get_mods() & pygame.KMOD_SHIFT else OFFSET_STEP_SMALL)
                    print(f"[DEBUG] OFFSET_SEC = {OFFSET_SEC:+.3f}s")
                if event.key == pygame.K_LEFTBRACKET:    # [
                    OFFSET_SEC -= (OFFSET_STEP_LARGE if pygame.key.get_mods() & pygame.KMOD_SHIFT else OFFSET_STEP_SMALL)
                    print(f"[DEBUG] OFFSET_SEC = {OFFSET_SEC:+.3f}s")

        # Allinea il timer al pos dell'audio (compensa la latenza del mixer)
        if music_started:
            pos_ms = pygame.mixer.music.get_pos()
            if pos_ms >= 0:
                if music_t0_ms is None:
                    music_t0_ms = pygame.time.get_ticks() - pos_ms
                    print(f"[CALIBRATE] music_t0_ms set @ {music_t0_ms} (pos={pos_ms} ms)")
                music_time = (pygame.time.get_ticks() - music_t0_ms) / 1000.0
            else:
                music_time = 0.0
        else:
            music_time = pygame.time.get_ticks() / 1000.0

        current_beats = max(0.0, (music_time + OFFSET_SEC) * BEATS_PER_SEC)

        # Avanza blocco
        while block_idx < len(change_beats) and current_beats >= change_beats[block_idx] - 1e-6:
            block_idx += 1

        # Log ingressi (HIT)
        if VERBOSE_HIT_LOG and block_idx != last_logged_idx:
            start_beat = 0.0 if block_idx == 0 else change_beats[block_idx-1]
            start_time_sec = start_beat * BEAT_SEC
            who = ""
            if block_idx < len(TIMELINE_BEATS):
                text = TIMELINE_BEATS[block_idx][1]
                who = (text.split(":")[0] if ":" in text else "").strip()
            print(f"[HIT] idx={block_idx:02d} | t={fmt_time(start_time_sec)} | beat={start_beat:8.3f} | who={who}")
            if abs(start_time_sec - ALIGN_DROP_SEC) < 0.020:        print(">>> REACHED DROP @ 0:26.000 (LUI START)")
            if abs(start_time_sec - REF_END_LUI_SEC) < 0.020:       print(">>> END LUI @ 0:52.960")
            if abs(start_time_sec - REF_END_IOCOS_SEC) < 0.020:     print(">>> END IO↔COS @ 1:19.440")
            if abs(start_time_sec - TRACK_END_SEC) < 0.020:         print(">>> END TRACK @ 1:32.500")
            last_logged_idx = block_idx

        # Fine scena
        if block_idx >= len(TIMELINE_BEATS):
            running = False
            screen.fill(BG_COLOR); pygame.display.flip()
            continue

        # --------------------------- RENDER -----------------------------------
        screen.fill(BG_COLOR)
        surf, rect = pre_surfs[block_idx]

        if block_idx == 0:
            # PRE-ROLL: logo in fade-in con glitch; scompare al drop
            if logo_surf is not None:
                # progress del fade basato sul tempo assoluto dell'audio (senza OFFSET)
                fade_prog = 0.0
                if 'music_time' in locals():
                    fade_prog = max(0.0, min(1.0, music_time / LOGO_FADE_IN_SEC))

                # frame glitched (solo durante fade, oppure sempre se vuoi)
                if GLITCH_ONLY_DURING_FADE and fade_prog >= 1.0:
                    frame = logo_surf
                else:
                    frame = glitch_logo_frame(logo_surf, fade_prog)

                # alpha del fade
                alpha = int(255 * fade_prog)
                frame = frame.copy()
                frame.set_alpha(alpha)

                screen.blit(frame, logo_rect)
            # niente testo durante il pre-roll
        else:
            # Dal drop in poi: NESSUN LOGO (sparisce di colpo), solo testo + glitch testuale
            if random.random() < 0.35:
                glitched = apply_glitch(surf)
                grect = glitched.get_rect(center=(WIDTH // 2, HEIGHT // 2))
                screen.blit(glitched, grect)
            else:
                screen.blit(surf, rect)

        if SHOW_GRID: draw_grid(screen, current_beats, WIDTH, HEIGHT)
        if SHOW_HUD:  draw_hud(screen, font_small, music_time, current_beats)

        pygame.display.flip()

    pygame.mixer.music.stop()
    if we_created_screen:
        pygame.quit()

# ------------------------------------------------------------------------------
if __name__ == "__main__":
    run_intro()
