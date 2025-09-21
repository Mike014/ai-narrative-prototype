# scenes/scene3.py
# -*- coding: utf-8 -*-

import os
import pygame
from pathlib import Path
from engine.entity_brain import EntityBrain

BASE_DIR = Path(__file__).resolve().parents[1]

def asset(*parts) -> str:
    return str(BASE_DIR.joinpath(*parts))

# --------------------------------------------------------------------------------------
# Avvio Scena 3 con timer
# --------------------------------------------------------------------------------------
def avvia_scena(screen, clock):
    print("Avvio scena 3...")

    pygame.mixer.set_num_channels(16)
    CHANNEL_GLITCH = pygame.mixer.Channel(14)

    screen_width, screen_height = screen.get_size()

    # ---------------- Audio ----------------
    ambient_music_path = asset("assets", "audio", "s3.wav")
    if os.path.exists(ambient_music_path):
        pygame.mixer.music.load(ambient_music_path)
        pygame.mixer.music.set_volume(0.25)
        pygame.mixer.music.play(-1)

    glitch_sound = pygame.mixer.Sound(asset("assets", "audio", "Glitch.ogg"))
    glitch_sound.set_volume(0.7)

    # ---------------- Grafica ----------------
    bg_path = asset("assets", "background", "scena3_bg.png")
    if os.path.exists(bg_path):
        background_image = pygame.image.load(bg_path).convert()
        background_image = pygame.transform.scale(background_image, (screen_width, screen_height))
    else:
        background_image = pygame.Surface((screen_width, screen_height))
        background_image.fill((0, 0, 0))

    # ---------------- Stato ENTITÀ ----------------
    # respond_prob 0.5 per cadenza più “cinematografica”
    entity = EntityBrain("entity_model", respond_prob=0.5)

    ENTITY_FONT = pygame.font.Font(asset("assets", "fonts", "entity.ttf"), 28)
    USER_FONT   = pygame.font.Font(asset("assets", "fonts", "fragile.ttf"), 24)
    ALERT_FONT  = pygame.font.Font(asset("assets", "fonts", "fragile.ttf"), 32)

    user_input = ""
    entity_response = ""
    show_entity = False
    entity_timer = 0
    entity_alpha = 255
    last_user_submit = False

    # ---------------- Conversazione (solo Utente ↔ ENTITÀ) ----------------
    # History locale: [(role, text)], role ∈ {"USER","ENTITA"}
    history = []
    MAX_TURNS = 8  # quante coppie tenere nel contesto del cervello

    def push(role: str, text: str):
        if not text:
            return
        history.append((role, text.strip()))
        # Mantieni solo le ultime MAX_TURNS*2 righe
        if len(history) > MAX_TURNS * 2:
            del history[0:len(history) - MAX_TURNS * 2]

    def build_context() -> str:
        # Etichette per il prompt del cervello: IO (utente) e ENTITÀ (modello)
        lines = []
        for role, text in history[-MAX_TURNS*2:]:
            if role == "USER":
                lines.append(f"IO: {text}")
            else:
                lines.append(f"ENTITÀ: {text}")
        return "\n".join(lines)

    # ---------------- Timer ----------------
    session_duration = 120000  # 2 minuti in ms
    start_time = pygame.time.get_ticks()

    # Traccia “ultimo parlato” di ENTITÀ (per calcolare silence_sec in secondi)
    entita_last_spoke_ms = start_time

    # Throttle locale scena
    MIN_GAP_AFTER_REPLY_SEC = 8.0     # attesa minima dopo una battuta di ENTITÀ
    MIN_GAP_AFTER_USER_SEC  = 1.5     # attesa minima tra due invii utente consecutivi
    next_allowed_speak_ms   = start_time
    last_user_enter_ms      = start_time - int(MIN_GAP_AFTER_USER_SEC * 1000) - 1

    # Gate probabilistico extra di scena (riduce ulteriormente la loquacità)
    SCENE_GATE_P = 0.85  # probabilità di far rispondere ENTITÀ

    # ---------------- Avviso iniziale ----------------
    alert_text = "ATTENZIONE: stai per comunicare con ENTITÀ.\nHai solo 2 minuti. Lei risponde quando vuole..."
    alert_shown = True
    alert_start = pygame.time.get_ticks()

    running = True
    while running:
        screen.blit(background_image, (0, 0))
        current_time = pygame.time.get_ticks()
        elapsed = current_time - start_time
        time_left = max(0, (session_duration - elapsed) // 1000)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            if not alert_shown and event.type == pygame.KEYDOWN:
                if event.key == pygame.K_RETURN:
                    last_user_submit = True
                    msg = user_input.strip()
                    if msg:
                        # --- Memoria: aggiungi la battuta dell'utente (sempre, anche se ENTITÀ tace) ---
                        push("USER", msg)

                        # --- Calcola silenzio (pygame usa ms -> converti in secondi) ---
                        silence_sec = max(0.0, (pygame.time.get_ticks() - entita_last_spoke_ms) / 1000.0)

                        # --- Throttle/Gate di scena ---
                        now_ms = pygame.time.get_ticks()

                        # evita risposte troppo ravvicinate dopo una battuta di ENTITÀ
                        if now_ms < next_allowed_speak_ms:
                            user_input = ""
                            entity_response = ""
                            show_entity = False
                            # non bloccare la partita, semplicemente “silenzio”
                            continue

                        # evita spam di invii troppo ravvicinati dell’utente
                        if (now_ms - last_user_enter_ms) < int(MIN_GAP_AFTER_USER_SEC * 1000):
                            user_input = ""
                            entity_response = ""
                            show_entity = False
                            continue

                        # gate probabilistico extra di scena
                        import random as _r
                        if _r.random() > SCENE_GATE_P:
                            user_input = ""
                            entity_response = ""
                            show_entity = False
                            # aggiorna timestamp dell'ultimo invio utente
                            last_user_enter_ms = now_ms
                            continue

                        # --- Tensione: baseline + ramp col silenzio + boost glitch (più morbidi) ---
                        base_tension = 0.22
                        ramp = min(0.25, (silence_sec / 45.0) * 0.25)       # crescita più lenta
                        glitch_boost = 0.05 if CHANNEL_GLITCH.get_busy() else 0.0
                        tension = max(0.0, min(1.0, base_tension + ramp + glitch_boost))

                        context = {"tension": tension, "silence_sec": silence_sec}

                        # --- Costruisci il “dialogo fino a questo punto” per ENTITÀ ---
                        dialog_context = build_context()

                        # --- Chiedi ad ENTITÀ (può anche tacere) ---
                        response = entity.generate_response(dialog_context, context=context, num_candidates=3)
                        user_input = ""
                        last_user_enter_ms = now_ms  # registriamo l'invio utente

                        if response:
                            CHANNEL_GLITCH.play(glitch_sound)
                            entity_response = response
                            show_entity = True
                            entity_timer = pygame.time.get_ticks()
                            entita_last_spoke_ms = entity_timer
                            entity_alpha = 255

                            # Memorizza risposta
                            push("ENTITA", response)

                            # Imposta il prossimo “permesso” a parlare (cooldown locale)
                            next_allowed_speak_ms = pygame.time.get_ticks() + int(MIN_GAP_AFTER_REPLY_SEC * 1000)
                        else:
                            entity_response = ""
                            show_entity = False
                    else:
                        user_input = ""

                elif event.key == pygame.K_BACKSPACE:
                    user_input = user_input[:-1]
                else:
                    if event.unicode and event.unicode.isprintable():
                        user_input += event.unicode

        # ---------------- Disegna avviso ----------------
        if alert_shown:
            elapsed_alert = (pygame.time.get_ticks() - alert_start) / 1000.0
            if elapsed_alert < 5:
                lines = alert_text.split("\n")
                for i, line in enumerate(lines):
                    text_surface = ALERT_FONT.render(line, True, (200, 50, 50))
                    rect = text_surface.get_rect(center=(screen_width // 2, screen_height // 2 + i * 40))
                    screen.blit(text_surface, rect)
            else:
                alert_shown = False

        else:
            # ---------------- Box input ----------------
            input_box_height = 40
            input_box_y = screen_height - 150
            input_box = pygame.Surface((screen_width - 100, input_box_height))
            input_box.set_alpha(200)
            input_box.fill((240, 240, 240))
            screen.blit(input_box, (50, input_box_y))

            input_surface = USER_FONT.render("> " + user_input, True, (10, 10, 10))
            screen.blit(input_surface, (60, input_box_y + 5))

            # ---------------- ENTITÀ o silenzio ----------------
            if show_entity:
                elapsed_entity = pygame.time.get_ticks() - entity_timer
                text_surface = ENTITY_FONT.render(entity_response, True, (255, 55, 55))
                text_surface.set_alpha(entity_alpha)
                text_rect = text_surface.get_rect(center=(screen_width // 2, screen_height // 2))
                screen.blit(text_surface, text_rect)

                if elapsed_entity > 3000:
                    entity_alpha -= 3
                    if entity_alpha <= 0:
                        show_entity = False
                        entity_response = ""
            else:
                if last_user_submit:
                    silence_surface = USER_FONT.render("...silenzio...", True, (180, 180, 180))
                    silence_rect = silence_surface.get_rect(center=(screen_width // 2, screen_height // 2))
                    screen.blit(silence_surface, silence_rect)

            # ---------------- Timer countdown ----------------
            timer_surface = USER_FONT.render(f"TEMPO RIMANENTE: {time_left}s", True, (200, 200, 200))
            screen.blit(timer_surface, (screen_width - 280, 20))

        # ---------------- Fine tempo ----------------
        if elapsed >= session_duration:
            fade_surface = pygame.Surface((screen_width, screen_height))
            for alpha in range(0, 255, 5):
                fade_surface.set_alpha(alpha)
                fade_surface.fill((0, 0, 0))
                screen.blit(fade_surface, (0, 0))
                pygame.display.flip()
                clock.tick(30)
            running = False

        pygame.display.flip()
        clock.tick(30)

    pygame.quit()
