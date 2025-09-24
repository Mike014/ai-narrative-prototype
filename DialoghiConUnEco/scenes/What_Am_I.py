# scenes/intro_poem.py
# -*- coding: utf-8 -*-
import sys
import random
from pathlib import Path
import numpy as np
import pygame

# ---------------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------------
BASE_DIR = Path(__file__).resolve().parents[1]
AUDIO_PATH = BASE_DIR / "assets" / "audio" / "what_am_I_song.wav"

WIDTH, HEIGHT = 1280, 720
FPS = 60
FONT_SIZE = 48
TEXT_COLOR = (245, 245, 250)
BG_COLOR = (0, 0, 0)

# Sync (80 BPM)
BPM = 80.8
BEAT_SEC = 60.0 / BPM          # 0.75 s
TOTAL_SEC = 105.0              # 1:45
TOTAL_BEATS = int(round(TOTAL_SEC / BEAT_SEC))  # 140 beat

# Offset iniziale (correggibile live con hotkeys)
OFFSET_SEC = 1.117   # >0 = ritarda i cambi; <0 = anticipa
OFFSET_STEP_SMALL = 0.010      # 10 ms
OFFSET_STEP_LARGE = 0.050      # 50 ms

# Grid/Metronomo (toggle con G)
SHOW_GRID = False
SHOW_HUD = True

# ---------------------------------------------------------------------------------
# Timeline beat-perfect (come concordato)
# ---------------------------------------------------------------------------------
TIMELINE_BEATS = [
    # 4 beat ciascuno (0:00–0:39)
    (4, "Mi sentivo strano, lontano da tutto."),
    (4, "Assente dalla realtà,"),
    (4, "come se il tempo"),
    (4, "non fosse il mio."),
    (4, "La guardavo dentro una sfera di cristallo,"),
    (4, "il collo che rimbalzava,"),
    (4, "vetro che tremava."),
    (4, "C’era quel ragazzo che capiva troppo,"),
    (4, "quello che ascolta il mondo"),
    (4, "e non lo spegne —"),
    (4, "maledetto perché"),
    (4, "sente ogni treno che passa."),
    (4, "Lei era in Honduras."),
    # 8 beat ciascuno (0:39–1:45)
    (8, "La mamma diceva che non dormiva,\nche la ricaduta"),
    (8, "le aveva mangiato i giorni.\nQuante volte l’ho sentito pronunciare,"),
    (8, "in questi tempi\nneri come piombo?"),
    (8, "Devo fare qualcosa, dicevo.\nLa giustizia"),
    (8, "coperta dal lamento collettivo."),
    (8, "Ma ci sono quelli che scelgono il male,\nche restano comodi dentro il disagio."),
    (8, "Io?\nSarò il primo ad andarmene."),
    (8, "Sarò quello che busserà alla porta del Primo,\ncon le mani sporche di domande."),
    (8, "E gli chiederò, con voce rotta:\n“Cosa c’è che non va in noi?”"),
    (8, "Forse lui riderà, piano, e dirà:\n“Siete solo umani.”"),
    (8, "E allora urlerò piano,\nperché la verità brucia come sale."),
]

# ---------------------------------------------------------------------------------
# Glitch "safe"
# ---------------------------------------------------------------------------------
def apply_glitch(surface: pygame.Surface) -> pygame.Surface:
    w, h = surface.get_width(), surface.get_height()
    if w < 4 or h < 4:
        return surface
    arr = pygame.surfarray.array3d(surface)
    dx = random.randint(-5, 5)
    dy = random.randint(-5, 5)
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

# ---------------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------------
def make_font(size=FONT_SIZE, bold=True) -> pygame.font.Font:
    try:
        return pygame.font.SysFont("DejaVu Sans", size, bold=bold)
    except Exception:
        try:
            return pygame.font.SysFont("Arial", size, bold=bold)
        except Exception:
            return pygame.font.Font(None, size)

def render_text_center(font: pygame.font.Font, text: str, color) -> tuple[pygame.Surface, pygame.Rect]:
    if "\n" in text:
        lines = text.split("\n")
        line_surfs = [font.render(ln if ln else " ", True, color) for ln in lines]
        total_h = sum(s.get_height() for s in line_surfs) + int((len(line_surfs) - 1) * (font.get_linesize() * 0.12))
        canvas = pygame.Surface((WIDTH, total_h), pygame.SRCALPHA)
        y = 0
        for ls in line_surfs:
            x = (WIDTH - ls.get_width()) // 2
            canvas.blit(ls, (x, y))
            y += ls.get_height() + int(font.get_linesize() * 0.12)
        rect = canvas.get_rect(center=(WIDTH // 2, HEIGHT // 2))
        return canvas, rect
    else:
        surf = font.render(text if text else " ", True, color)
        rect = surf.get_rect(center=(WIDTH // 2, HEIGHT // 2))
        return surf, rect

def cumulative_change_beats(timeline_beats):
    beats = []
    acc = 0
    for b, _ in timeline_beats:
        acc += b
        beats.append(acc)
    return beats  # es. [4,8,12,...,140]

# ---------------------------------------------------------------------------------
# Metronomo visivo + HUD
# ---------------------------------------------------------------------------------
def draw_grid(screen: pygame.Surface, current_beats: float):
    beat_num = int(current_beats)
    phase = current_beats - beat_num   # 0..1
    # flash su ogni beat
    alpha = int(120 * (1.0 - phase) ** 2)
    bar = pygame.Surface((WIDTH, 2), pygame.SRCALPHA)
    bar.fill((255, 255, 255, max(0, min(120, alpha))))
    screen.blit(bar, (0, HEIGHT - 10))
    # downbeat ogni 4 beat
    if beat_num % 4 == 0 and phase < 0.15:
        ring = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        ring.fill((255, 255, 255, 12))
        screen.blit(ring, (0, 0), special_flags=pygame.BLEND_ADD)

# def draw_hud(screen: pygame.Surface, current_beats: float, next_change_beat: int | None, offset_sec: float):
#     hud_font = make_font(size=18, bold=False)
#     lines = [
#         f"Beat: {current_beats:.2f}",
#         f"Offset: {int(offset_sec*1000):+d} ms",
#     ]
#     if next_change_beat is not None:
#         lines.append(f"Next change @ beat: {next_change_beat}")
#     y = 10
#     for s in lines:
#         surf = hud_font.render(s, True, (180, 190, 205))
#         screen.blit(surf, (10, y))
#         y += 20

# ---------------------------------------------------------------------------------
# Scena
# ---------------------------------------------------------------------------------
def run_intro():
    global OFFSET_SEC, SHOW_GRID, SHOW_HUD

    pygame.init()
    pygame.mixer.pre_init(44100, -16, 2, 512)
    pygame.mixer.init()

    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("Solo Umani - Intro (80 BPM beat-locked)")

    clock = pygame.time.Clock()
    font = make_font()

    # Pre-render testo
    pre_surfs = []
    for _, text in TIMELINE_BEATS:
        surf, rect = render_text_center(font, text, TEXT_COLOR)
        pre_surfs.append((surf, rect))

    # Soglie cumulative in BEATS
    change_beats = cumulative_change_beats(TIMELINE_BEATS)  # es. [4,8,12,...,140]

    # Musica
    music_started = False
    if AUDIO_PATH.exists():
        try:
            pygame.mixer.music.load(str(AUDIO_PATH))
            pygame.mixer.music.play()
            music_started = True
        except Exception as e:
            print("Audio non caricato:", e)

    block_idx = 0
    running = True

    while running:
        _dt = clock.tick(FPS) / 1000.0

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
                pygame.mixer.music.stop()
                pygame.quit()
                sys.exit()
            if event.type == pygame.KEYDOWN:
                # exit/skip
                if event.key in (pygame.K_ESCAPE, pygame.K_RETURN, pygame.K_SPACE):
                    running = False
                # toggle
                if event.key == pygame.K_g:
                    SHOW_GRID = not SHOW_GRID
                if event.key == pygame.K_h:
                    SHOW_HUD = not SHOW_HUD
                # fine adjust offset
                if event.key == pygame.K_RIGHTBRACKET:   # ]
                    if pygame.key.get_mods() & pygame.KMOD_SHIFT:
                        OFFSET_SEC += OFFSET_STEP_LARGE
                    else:
                        OFFSET_SEC += OFFSET_STEP_SMALL
                if event.key == pygame.K_LEFTBRACKET:    # [
                    if pygame.key.get_mods() & pygame.KMOD_SHIFT:
                        OFFSET_SEC -= OFFSET_STEP_LARGE
                    else:
                        OFFSET_SEC -= OFFSET_STEP_SMALL

        # Tempo musica -> beat assoluti (con offset)
        if music_started:
            music_time = max(0.0, pygame.mixer.music.get_pos() / 1000.0)
        else:
            music_time = pygame.time.get_ticks() / 1000.0
        current_beats = (music_time + OFFSET_SEC) / BEAT_SEC  # beat float dall'inizio

        # Avanza blocco secondo BEATS (niente secondi → niente drift)
        while block_idx < len(change_beats) and current_beats >= change_beats[block_idx] - 1e-6:
            block_idx += 1

        # Fine scena
        if block_idx >= len(TIMELINE_BEATS):
            running = False
            screen.fill(BG_COLOR)
            pygame.display.flip()
            continue

        # Render
        screen.fill(BG_COLOR)

        surf, rect = pre_surfs[block_idx]
        text_is_empty = (surf.get_width() < 2 or surf.get_height() < 2)
        if not text_is_empty:
            if random.random() < 0.4:
                glitched = apply_glitch(surf)
                grect = glitched.get_rect(center=(WIDTH // 2, HEIGHT // 2))
                screen.blit(glitched, grect)
            else:
                screen.blit(surf, rect)

        if SHOW_GRID:
            draw_grid(screen, current_beats)

        # if SHOW_HUD:
        #     next_change = change_beats[block_idx] if block_idx < len(change_beats) else None
        #     draw_hud(screen, current_beats, next_change, OFFSET_SEC)

        pygame.display.flip()

    pygame.mixer.music.stop()

# ---------------------------------------------------------------------------------
if __name__ == "__main__":
    run_intro()
