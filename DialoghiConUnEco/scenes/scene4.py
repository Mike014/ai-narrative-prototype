# scenes/scene4.py
# -*- coding: utf-8 -*-
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import math
import random
from pathlib import Path
from typing import Optional

import pygame

from engine.dialog_manager import DialogManager
from engine.entity_director import EntityDirector

# --------------------------------------------------------------------------------------
# Impostazione percorsi robusti
# --------------------------------------------------------------------------------------
BASE_DIR = Path(__file__).resolve().parents[1]
def asset(*parts) -> str:
    return str(BASE_DIR.joinpath(*parts))


# --------------------------------------------------------------------------------------
# Dialogo (solo IO & COSCIENZA) — NON MODIFICARE
# --------------------------------------------------------------------------------------
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


# --------------------------------------------------------------------------------------
# Helpers grafici
# --------------------------------------------------------------------------------------
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


# --------------------------------------------------------------------------------------
# Avvio Scena 4 (musica singola in loop @ 81 BPM) + FINALE GLITCH
# --------------------------------------------------------------------------------------
def avvia_scena(screen, clock):
    print("Avvio scena 4...")

    # Audio
    pygame.mixer.set_num_channels(16)
    music_path = asset("assets", "audio", "what_am_I.wav")
    if os.path.exists(music_path):
        try:
            pygame.mixer.music.load(music_path)
            pygame.mixer.music.set_volume(0.55)
            pygame.mixer.music.play(-1, fade_ms=900)  # loop con fade-in
        except Exception as e:
            print("[Scene4] Impossibile caricare/riprodurre what_am_I.wav:", e)
    else:
        print("[Scene4] Audio non trovato:", music_path)

    # Tempo/griglia (per eventuali sync)
    BPM = 81.0
    MS_PER_BEAT = 60000.0 / BPM
    BAR_MS = int(MS_PER_BEAT * 4)

    # Grafica (background della scena durante il dialogo)
    w, h = screen.get_size()
    bg_path = asset("assets", "background", "what_am_I.png")
    if os.path.exists(bg_path):
        bg = pygame.image.load(bg_path).convert()
        bg = pygame.transform.scale(bg, (w, h))
    else:
        bg = pygame.Surface((w, h)); bg.fill((10, 10, 12))

    # Dialog manager
    dialog = DialogManager(
        io_font_path=asset("assets", "fonts", "fragile.ttf"),
        coscienza_font_path=asset("assets", "fonts", "reflective.ttf"),
        entity_font_path=asset("assets", "fonts", "entity.ttf"),
        font_size=28, screen_width=w, screen_height=h
    )
    dialog.load_dialog(get_scene())

    # Director (ENTITÀ fuori scena)
    director = EntityDirector(asset)

    def build_context() -> str:
        lines = []
        for line in dialog.dialog_lines[: dialog.current_line + 1]:
            if len(line) == 3: spk, pre, txt = line
            else: spk, txt = line; pre = f"{spk}:"
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
                    # Regia esterna (ENTITÀ)
                    chans = director.score_channels(build_context())
                    if chans.get("oppressione", 0.0) > 0.75:
                        director.queue_fake_toast("Pressione temporale elevata.", dialog_context=build_context())
                    director.make_caption(chans)
                else:
                    # Fine dialogo → finale glitch (chiude tutto)
                    _finale_glitch(screen, clock)
                    return  # non proseguire oltre: il finale chiude il processo

        # Tick per auto-chiusura nota/gestioni director
        director.draw_fake_toasts(screen)

        # DRAW
        screen.blit(bg, (0, 0))
        dialog.draw(screen)

        pygame.display.flip()
        clock.tick(30)

    # Se si esce senza finale (ad es. chiusura finestra durante il dialogo)
    try:
        pygame.mixer.music.fadeout(500)
    except Exception:
        pass
    pygame.quit()


# --------------------------------------------------------------------------------------
# Sequenza finale: GLITCH "What Am I?" + suono Ti_Vedo2.wav → chiusura immediata
# --------------------------------------------------------------------------------------
def _finale_glitch(screen, clock):
    import platform

    # Ducking musica subito
    try:
        pygame.mixer.music.set_volume(0.07)
    except Exception:
        pass

    # SFX
    sfx_path = asset("assets", "audio", "Ti_Vedo2.wav")
    sfx = None
    if os.path.exists(sfx_path):
        try:
            sfx = pygame.mixer.Sound(sfx_path)
        except Exception as e:
            print("[Scene4] Impossibile caricare Ti_Vedo.wav:", e)

    # Font grande per il testo glitch (~18% H)
    H = screen.get_height()
    try:
        glitch_font = pygame.font.Font(asset("assets", "fonts", "entity.ttf"), max(48, int(H * 0.18)))
    except Exception:
        glitch_font = pygame.font.SysFont("consolas", max(48, int(H * 0.18)))

    # Avvia SFX immediatamente
    if sfx:
        try:
            ch = pygame.mixer.find_channel() or pygame.mixer.Channel(15)
            ch.play(sfx)
        except Exception:
            pass

    # 5 secondi netti di schermo nero + testo glitch
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
                # Chiusura immediata
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
