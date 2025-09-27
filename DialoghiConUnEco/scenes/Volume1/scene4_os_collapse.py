# scenes/Volume1/scene4_os_collapse.py
# -*- coding: utf-8 -*-

import sys
import os
import math
import random
import platform
import subprocess
from pathlib import Path

import pygame
from dotenv import load_dotenv

from engine.dialog_manager import DialogManager
from engine.entity_director import EntityDirector

# -----------------------------------------------------------------------------
# Env (per eventuali API key o config usate da EntityDirector/EntityBrain)
# -----------------------------------------------------------------------------
load_dotenv()

# -----------------------------------------------------------------------------
# Project root discovery (robusto a spostamenti di file)
# -----------------------------------------------------------------------------
def find_project_root(start: Path) -> Path:
    p = start
    for _ in range(6):  # risali max 6 livelli
        if (p / "assets").exists() and (p / "engine").exists():
            return p
        p = p.parent
    return start  # fallback

THIS_FILE = Path(__file__).resolve()
BASE_DIR = find_project_root(THIS_FILE)
ASSETS_DIR = BASE_DIR / "assets"

def asset_path(*parts) -> str:
    """Path assoluto sotto assets/"""
    return str(ASSETS_DIR.joinpath(*parts))

def project_path(*parts) -> str:
    """Path assoluto dalla root del progetto (compat per EntityDirector)"""
    return str(BASE_DIR.joinpath(*parts))

# -----------------------------------------------------------------------------
# Dialogo (solo IO & COSCIENZA) — NON MODIFICARE
# -----------------------------------------------------------------------------
def get_scene():
    return [
        ("IO", "Disteso sul materasso, pancia in giù."),
        ("IO", "Orecchie in acufene."),
        ("IO", "La musica metal rompeva lo schema del trigger fisso."),
        ("IO", "Ti pensavo con lui."),
        ("IO", "Ti pensavo con me."),
        ("COSCIENZA", "Il confronto brucia più dell’assenza."),
        ("IO", "Sarei stato adatto?"),
        ("IO", "Sarei stato?"),
        ("COSCIENZA", "La domanda non ha risposta, eppure ti lacera."),
        ("IO", "Un’ossessione: un braccialetto rosso, una psichiatra —"),
        ("IO", "«Hai sofferto, forse dovevi farlo prima»."),
        ("IO", "Lo sfogo."),
        ("IO", "La ferita del trauma."),
        ("COSCIENZA", "Ogni cicatrice vuole restare viva nel ricordo."),
        ("IO", "Sei tu, Coscienza? Tu sei con me? Il richiamo a LEI."),
        ("COSCIENZA", "Io resto. Ma LEI non c’è."),
        ("IO", "Il pianto irrisolto, appoggiato sul pavimento; con forza premevo sulla tempia."),
        ("IO", "Tutto scuro. Grigio. Puzzo di vuoto."),
        ("COSCIENZA", "Nel vuoto cerchi il senso, ma trovi solo eco."),
        ("IO", "Sono una persona molto triste."),
        ("IO", "Speravo fossi la mia luce."),
        ("IO", "Non dimenticarmi, ti prego."),
        ("IO", "Non dimenticare la mia collana."),
        ("COSCIENZA", "La luce non salva, solo rivela ciò che sei."),
        ("IO", "L’ho sentita — Coscienza, LEI — come un suono in loop, un tema che torna:"),
        ("IO", "quattro accordi che finiscono in LA maggiore, la musica che diventa lamento."),
        ("COSCIENZA", "Anche l’illusione ha un ritmo, e tu lo segui come fosse reale."),
        ("IO", "Come posso dimenticare qualcuno che non è mai esistito nella mia vita,"),
        ("IO", "ma che amo più di me stesso?"),
        ("COSCIENZA", "L’amore impossibile è il più fedele: non muore nella realtà."),
    ]

# -----------------------------------------------------------------------------
# Helpers grafici
# -----------------------------------------------------------------------------
def render_text_with_outline(text, font, text_color, outline_color=(0, 0, 0)):
    base = font.render(text, True, text_color)
    outline = pygame.Surface((base.get_width() + 2, base.get_height() + 2), pygame.SRCALPHA)
    for dx in (-1, 0, 1):
        for dy in (-1, 0, 1):
            if dx or dy:
                shadow = font.render(text, True, outline_color)
                outline.blit(shadow, (1 + dx, 1 + dy))
    outline.blit(base, (1, 1))
    return outline

def draw_glitch_text(surface, text, center, font, tick_ms):
    """
    Effetto glitch semplice: chromatic shift + jitter + scanlines + flicker alpha.
    """
    rnd = random.Random(tick_ms // 33)  # seed ~30 FPS
    jitter = lambda a: rnd.randint(-a, a)

    base = font.render(text, True, (230, 230, 230))
    w, h = base.get_size()

    def tint(surf, color):
        s = surf.copy()
        s.fill(color + (0,), special_flags=pygame.BLEND_RGBA_MULT)
        return s

    red = tint(base, (255, 60, 60))
    cyn = tint(base, (60, 255, 255))

    scale_amt = 1.0 + 0.02 * math.sin(tick_ms * 0.02)
    sw = max(1, int(w * scale_amt)); sh = max(1, int(h * scale_amt))
    base_s = pygame.transform.smoothscale(base, (sw, sh))
    red_s  = pygame.transform.smoothscale(red,  (sw, sh))
    cyn_s  = pygame.transform.smoothscale(cyn,  (sw, sh))

    cx, cy = center
    pos  = (cx - sw // 2, cy - sh // 2)
    posR = (pos[0] + jitter(3) - 2, pos[1] + jitter(2))
    posC = (pos[0] - jitter(3) + 2, pos[1] - jitter(2))

    alpha = 210 + int(40 * math.sin(tick_ms * 0.025))
    for s in (red_s, cyn_s, base_s):
        s.set_alpha(alpha)

    surface.blit(red_s, posR)
    surface.blit(cyn_s, posC)
    surface.blit(base_s, pos)

    # scanlines
    sl_h = 2
    scan = pygame.Surface((surface.get_width(), sl_h), pygame.SRCALPHA)
    scan.fill((0, 0, 0, 36))
    for y in range(0, surface.get_height(), 6):
        surface.blit(scan, (0, y))

def load_background(screen):
    """Carica background con fallback sensati per la scena."""
    candidates = [
        ("background", "what_am_I.png"),
        ("background", "logo_what_am_i.PNG"),
        ("background", "room.png"),
        ("background", "mac.png"),
    ]
    for parts in candidates:
        p = ASSETS_DIR.joinpath(*parts)
        if p.exists():
            img = pygame.image.load(str(p)).convert()
            return pygame.transform.scale(img, screen.get_size()), str(p)
    surf = pygame.Surface(screen.get_size())
    surf.fill((10, 10, 12))
    return surf, "(fill dark)"

# -----------------------------------------------------------------------------
# Avvio Scena 4 (musica in loop @ 81 BPM) + FINALE GLITCH
# -----------------------------------------------------------------------------
def avvia_scena(screen, clock):
    print("[DEBUG][SCENA4] BASE_DIR:", BASE_DIR)
    print("[DEBUG][SCENA4] ASSETS_DIR:", ASSETS_DIR)

    # Audio
    pygame.mixer.set_num_channels(16)
    music_path = asset_path("audio", "what_am_I.wav")
    if os.path.exists(music_path):
        try:
            pygame.mixer.music.load(music_path)
            pygame.mixer.music.set_volume(0.55)
            pygame.mixer.music.play(-1, fade_ms=900)  # loop con fade-in
        except Exception as e:
            print("[SCENA4] Impossibile caricare/riprodurre what_am_I.wav:", e)
    else:
        print("[SCENA4] Audio non trovato:", music_path)

    # Tempo/griglia (per eventuale sync)
    BPM = 81.0
    MS_PER_BEAT = 60000.0 / BPM
    BAR_MS = int(MS_PER_BEAT * 4)
    _ = (MS_PER_BEAT, BAR_MS)  # mantenuti per eventuale futura sincronizzazione

    # Grafica (background)
    w, h = screen.get_size()
    background_image, chosen_bg = load_background(screen)
    print(f"[DEBUG][SCENA4] Background: {chosen_bg}")

    # Dialog manager (mantengo tua firma con width/height se supportata)
    io_font_path     = ASSETS_DIR / "fonts" / "fragile.ttf"
    cosc_font_path   = ASSETS_DIR / "fonts" / "reflective.ttf"
    entity_font_path = ASSETS_DIR / "fonts" / "entity.ttf"

    try:
        dialog = DialogManager(
            io_font_path=str(io_font_path),
            coscienza_font_path=str(cosc_font_path),
            entity_font_path=str(entity_font_path),
            font_size=28, screen_width=w, screen_height=h
        )
    except TypeError:
        # fallback se DialogManager non accetta screen_width/height
        dialog = DialogManager(
            io_font_path=str(io_font_path),
            coscienza_font_path=str(cosc_font_path),
            entity_font_path=str(entity_font_path),
            font_size=28
        )
    dialog.load_dialog(get_scene())

    # Director (ENTITÀ fuori scena). Gli passo una funzione compatibile con la tua vecchia `asset`.
    director = EntityDirector(project_path)

    def build_context() -> str:
        lines = []
        for line in dialog.dialog_lines[: dialog.current_line + 1]:
            if isinstance(line, (list, tuple)):
                if len(line) == 3:
                    spk, pre, txt = line
                elif len(line) == 2:
                    spk, txt = line; pre = f"{spk}:"
                else:
                    continue
                lines.append(f"{pre} {txt}".strip())
        return "\n".join(lines)

    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            if event.type == pygame.KEYDOWN and event.key == pygame.K_RETURN:
                if dialog.current_line < len(dialog.dialog_lines) - 1:
                    dialog.next_line()
                    # Regia esterna (ENTITÀ come OS): punzecchia con notifiche/caption
                    chans = director.score_channels(build_context())
                    if chans.get("oppressione", 0.0) > 0.75:
                        director.queue_fake_toast("Pressione temporale elevata.", dialog_context=build_context())
                    director.make_caption(chans)
                else:
                    # Fine dialogo → finale glitch (chiude tutto)
                    _finale_glitch(screen, clock)
                    return  # il finale esce dal processo

        # DRAW
        screen.blit(background_image, (0, 0))
        dialog.draw(screen)
        director.draw_fake_toasts(screen)  # disegna eventuali toasts sovrapposti

        pygame.display.flip()
        clock.tick(30)

    # Uscita senza finale (chiusura finestra)
    try:
        pygame.mixer.music.fadeout(500)
    except Exception:
        pass
    pygame.quit()

# -----------------------------------------------------------------------------
# Sequenza finale: GLITCH "WHAT AM I?" + Ti_Vedo2.wav → uscita dura
# -----------------------------------------------------------------------------
def _finale_glitch(screen, clock):
    # Ducking musica subito
    try:
        pygame.mixer.music.set_volume(0.07)
    except Exception:
        pass

    # SFX
    sfx_path = asset_path("audio", "Ti_Vedo2.wav")
    sfx = None
    if os.path.exists(sfx_path):
        try:
            sfx = pygame.mixer.Sound(sfx_path)
        except Exception as e:
            print("[SCENA4] Impossibile caricare Ti_Vedo2.wav:", e)

    # Font grande per il testo glitch (~18% H)
    H = screen.get_height()
    try:
        glitch_font = pygame.font.Font(asset_path("fonts", "entity.ttf"), max(48, int(H * 0.18)))
    except Exception:
        glitch_font = pygame.font.SysFont("consolas", max(48, int(H * 0.18)))

    # Avvia SFX immediatamente
    if sfx:
        try:
            ch = pygame.mixer.find_channel() or pygame.mixer.Channel(15)
            ch.play(sfx)
        except Exception:
            pass

    # 3 secondi di schermo nero + testo glitch
    duration_ms = 3000
    t0 = pygame.time.get_ticks()
    center = (screen.get_width() // 2, screen.get_height() // 2)
    BLACK = (0, 0, 0)

    while True:
        now = pygame.time.get_ticks()
        if now - t0 >= duration_ms:
            break

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                try:
                    pygame.mixer.music.stop()
                    pygame.mixer.stop()
                except Exception:
                    pass
                pygame.quit()
                sys.exit(0)

        screen.fill(BLACK)
        draw_glitch_text(screen, "WHAT AM I?", center, glitch_font, now)

        pygame.display.flip()
        clock.tick(60)

    # Stop immediato e uscita dura
    try:
        pygame.mixer.music.stop()
        pygame.mixer.stop()
    except Exception:
        pass

    pygame.quit()
    try:
        sys.exit(0)
    finally:
        os._exit(0)
