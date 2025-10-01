# scenes/Volume1/scene2_profuma_il_grigio.py
# -*- coding: utf-8 -*-
import os
import random
import platform
import subprocess
from pathlib import Path

import pygame

from engine.dialog_manager import DialogManager
from engine.entity_brain import EntityBrain

from dotenv import load_dotenv
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
    return str(ASSETS_DIR.joinpath(*parts))

# -----------------------------------------------------------------------------
# Scena 2: "Profumare il Grigio" (poesia intera + interventi dinamici)
# -----------------------------------------------------------------------------
def get_scene():
    return [
        # --- Poesia: blocco 1 (intera, senza tagli) ---
        ("IO", "Mi sento bombardato"),
        ("IO", "da giudizi intrisi di ipocrisia."),
        ("IO", "Forse è solo"),
        ("IO", "il mio stato di allarme"),
        ("IO", "che si attiva."),
        ("IO", "Passo il tempo a scrivere poesie,"),
        ("IO", "cercando un significato"),
        ("IO", "dal mio profondo."),

        # Intervento dinamico (solo LUI)
        ("LUI", "Non stai cercando, stai scavando nella carne."),

        # --- Poesia: blocco 2 ---
        ("IO", "Mi piace usare parole estreme,"),
        ("IO", "maledette,"),
        ("IO", "perché in realtà mi sento così."),
        ("IO", "Racchiuso nel mio cerchio,"),
        ("IO", "inchinato sul diario,"),
        ("IO", "mentre il resto del mondo"),
        ("IO", "geme e si scuote."),

        # Intervento dinamico (solo COSCIENZA)
        ("COSCIENZA", "Sei tu che ti isoli, non loro che ti respingono."),

        # --- Poesia: blocco 3 ---
        ("IO", "Li guardo da fuori,"),
        ("IO", "come una razza che non mi appartiene."),
        ("IO", "O forse è soltanto"),
        ("IO", "il bisogno di essere amato"),
        ("IO", "e compreso."),
        ("IO", "Creo mostri,"),
        ("IO", "creature che nascono"),
        ("IO", "dal mio modo di ribellarmi"),
        ("IO", "a ciò che non mi accetta."),
        ("IO", "O forse"),
        ("IO", "al mio io"),
        ("IO", "che non mi accetta."),

        # Intervento dinamico (solo LUI)
        ("LUI", "Io sono quel “io” che non ti accetta."),

        # --- Separatore originale ---
        ("IO", "---"),

        # --- Poesia: blocco 4 ---
        ("IO", "È tutto lento qui."),
        ("IO", "Non scorre nulla."),
        ("IO", "Solo frasi,"),
        ("IO", "parole astratte."),
        ("IO", "Nella stanza buia,"),
        ("IO", "grigia,"),
        ("IO", "poco soleggiata,"),
        ("IO", "avevo bisogno"),
        ("IO", "del profumo di vaniglia."),

        # Intervento dinamico (solo COSCIENZA)
        ("COSCIENZA", "Un ricordo che cerchi di trattenere."),

        # --- Poesia: blocco 5 ---
        ("IO", "O di ciliegio."),
        ("IO", "Del sapore del rossetto,"),
        ("IO", "dolce sulla lingua."),
        ("IO", "Del profumo dei capelli,"),
        ("IO", "fiore nell’aria."),
        ("IO", "Dell’essenza che resta sul petto"),
        ("IO", "dopo averla respirata"),
        ("IO", "per ore"),
        ("IO", "sul suo collo."),

        # Intervento dinamico (solo LUI)
        ("LUI", "È ossessione, non memoria."),

        # --- Separatore originale ---
        ("IO", "---"),

        # --- Poesia: blocco finale ---
        ("IO", "Il grigiore"),
        ("IO", "è parte di me."),
        ("IO", "E lo profumo"),
        ("IO", "con quello che posso."),

        # Chiusura a due voci (ordine intenzionale; nessun trigger finale)
        ("COSCIENZA", "Con amore."),
        ("LUI", "Con veleno."),
    ]

# -----------------------------------------------------------------------------
# Helpers grafici
# -----------------------------------------------------------------------------
def render_text_with_outline(text, font, text_color, outline_color=(0, 0, 0)):
    base = font.render(text, True, text_color)
    outline = pygame.Surface((base.get_width() + 2, base.get_height() + 2), pygame.SRCALPHA)
    for dx in [-1, 0, 1]:
        for dy in [-1, 0, 1]:
            if dx != 0 or dy != 0:
                outline.blit(font.render(text, True, outline_color), (1 + dx, 1 + dy))
    outline.blit(base, (1, 1))
    return outline

# -----------------------------------------------------------------------------
# Caricamento sicuro background (con fallback)
# -----------------------------------------------------------------------------
def load_background(screen):
    candidates = [
        ("background", "scene1_background.jpg"),
        ("background", "room.png"),
        ("background", "mac.png"),
    ]
    for parts in candidates:
        p = ASSETS_DIR.joinpath(*parts)
        if p.exists():
            img = pygame.image.load(str(p)).convert()
            return pygame.transform.scale(img, screen.get_size()), str(p)
    # fallback: nero pieno
    surf = pygame.Surface(screen.get_size())
    surf.fill((0, 0, 0))
    return surf, "(fill black)"

# -----------------------------------------------------------------------------
# Entry della scena
# -----------------------------------------------------------------------------
def avvia_scena(screen, clock):
    print(f"[DEBUG] BASE_DIR: {BASE_DIR}")
    print(f"[DEBUG] ASSETS_DIR: {ASSETS_DIR}")

    # Mixer
    pygame.mixer.set_num_channels(16)
    CHANNEL_GLITCH = pygame.mixer.Channel(14)

    # Audio
    ambient_music_path = asset_path("audio", "Ambient.ogg")
    glitch_path = asset_path("audio", "Glitch.ogg")

    pygame.mixer.music.load(ambient_music_path)
    pygame.mixer.music.set_volume(0.5)
    pygame.mixer.music.play(-1)

    glitch_sound = pygame.mixer.Sound(glitch_path)
    glitch_sound.set_volume(0.7)

    # Background
    background_image, chosen_bg = load_background(screen)
    print(f"[DEBUG] Background: {chosen_bg}")

    # Font reali presenti
    io_font_path = ASSETS_DIR / "fonts" / "fragile.ttf"
    cosc_font_path = ASSETS_DIR / "fonts" / "reflective.ttf"
    entity_font_path = ASSETS_DIR / "fonts" / "entity.ttf"

    # Dialog Manager (stessa configurazione della scena1)
    dialog_manager = DialogManager(
        io_font_path=str(io_font_path),
        coscienza_font_path=str(cosc_font_path),
        entity_font_path=str(entity_font_path),
        font_size=28
    )
    dialog_manager.load_dialog(get_scene())

    # Font per overlay ENTITÀ e LUI (ibrido)
    ENTITY_FONT = pygame.font.Font(str(entity_font_path), 26)
    LUI_FONT_IO = pygame.font.Font(str(io_font_path), 28)
    LUI_FONT_COSC = pygame.font.Font(str(cosc_font_path), 28)
    LUI_FONT_ENT = pygame.font.Font(str(entity_font_path), 28)

    # Stato ENTITÀ (solo overlay temporaneo; nessun file/log/“TI VEDO”)
    entity = EntityBrain("entity_model")
    entity_active = False
    entity_response = ""
    entity_timer = 0
    entity_alpha = 255

    # Funzione: overlay “ibrido” per LUI (sovrappone i tre font)
    def draw_lui_hybrid_overlay(surface, text: str):
        if not text:
            return
        full_text = "LUI: " + text
        s_io = LUI_FONT_IO.render(full_text, True, (235, 235, 235))
        s_cosc = LUI_FONT_COSC.render(full_text, True, (180, 210, 255))
        s_ent = LUI_FONT_ENT.render(full_text, True, (255, 80, 80))

        w = max(s_io.get_width(), s_cosc.get_width(), s_ent.get_width()) + 6
        h = max(s_io.get_height(), s_cosc.get_height(), s_ent.get_height()) + 6
        combo = pygame.Surface((w, h), pygame.SRCALPHA)

        combo.blit(s_cosc, (1, 1))
        combo.blit(s_ent, (3, 2))
        combo.blit(s_io, (2, 2))

        rect = combo.get_rect(center=(surface.get_width() // 2, surface.get_height() - 140))
        surface.blit(combo, rect)

    running = True
    while running:
        screen.blit(background_image, (0, 0))

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            if event.type == pygame.KEYDOWN and event.key == pygame.K_RETURN:
                last_idx = len(dialog_manager.dialog_lines) - 1
                # Alla fine: nessun trigger, nessun file, nessun “TI VEDO”.
                if dialog_manager.current_line == last_idx:
                    running = False  # chiudi scena in modo pulito
                else:
                    dialog_manager.next_line()

                    # Intervento casuale ENTITÀ su battute di IO (overlay temporaneo)
                    if dialog_manager.current_line > 0:
                        prev = dialog_manager.dialog_lines[dialog_manager.current_line - 1]
                        if isinstance(prev, (list, tuple)):
                            speaker = prev[0] if len(prev) >= 1 else None
                            text = prev[1] if len(prev) >= 2 else ""
                        else:
                            speaker, text = None, ""

                        if speaker == "IO" and not entity_active and random.random() < 0.3:
                            risposta = entity.generate_response(f"{text}\nENTITÀ:")
                            if risposta:
                                CHANNEL_GLITCH.play(glitch_sound)
                                entity_active = True
                                entity_response = risposta
                                entity_timer = pygame.time.get_ticks()
                                entity_alpha = 255

        # Disegno dialoghi (default DialogManager)
        dialog_manager.draw(screen)

        # Overlay ENTITÀ con fade-out (solo overlay, nessun side-effect)
        if entity_active:
            elapsed = pygame.time.get_ticks() - entity_timer
            full_text = "ENTITÀ: " + entity_response.strip().capitalize()
            text_surface = render_text_with_outline(full_text, ENTITY_FONT, (255, 55, 55))
            text_surface.set_alpha(entity_alpha)
            rect = text_surface.get_rect(center=(screen.get_width() // 2, screen.get_height() // 2 - 100))
            screen.blit(text_surface, rect)

            if elapsed > 3000:
                entity_alpha -= 3
                if entity_alpha <= 0:
                    entity_alpha = 0
                    entity_active = False
                    entity_response = ""

        # Overlay font ibrido per LUI
        try:
            if 0 <= dialog_manager.current_line < len(dialog_manager.dialog_lines):
                spk, txt = dialog_manager.dialog_lines[dialog_manager.current_line]
                if spk == "LUI":
                    draw_lui_hybrid_overlay(screen, txt)
        except Exception:
            pass

        pygame.display.flip()
        clock.tick(30)

    pygame.quit()
