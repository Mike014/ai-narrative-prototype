# scenes/scene2.py
# -*- coding: utf-8 -*-

import os
import random
import platform
import subprocess
from pathlib import Path

import pygame

from engine.dialog_manager import DialogManager
from engine.entity_brain import EntityBrain


# --------------------------------------------------------------------------------------
# Impostazione percorsi robusti rispetto alla working directory
# --------------------------------------------------------------------------------------
BASE_DIR = Path(__file__).resolve().parents[1]


def asset(*parts) -> str:
    return str(BASE_DIR.joinpath(*parts))


# --------------------------------------------------------------------------------------
# Scena 2
# --------------------------------------------------------------------------------------
def get_scene():
    return [
        ("IO", "Poche ore al mio compleanno."),
        ("IO", "L’attesa prima della celebrazione della propria nascita."),
        ("IO", "Mi sono sempre chiesto:"),
        ("IO", "scatta a mezzanotte, o nel momento preciso in cui hai aperto gli occhi,"),
        ("IO", "respirato aria con polmoni nuovi,"),
        ("IO", "sentito sulla pelle quelle piccole molecole pruriginose che ti dicono che sei vivo?"),
        ("COSCIENZA", "Il primo respiro segna l'inizio, non l'orologio."),
        ("IO", "Quella sensazione di 'accensione'. Click. Sistema operativo: installato."),
        ("COSCIENZA", "Un boot che nessuno ricorda, ma tutti hanno fatto."),
        ("IO", "E prima? Cosa c’era? Qualcosa di simile alla morte?"),
        ("IO", "Una stanza totalmente buia, vuota, senza eco."),
        ("COSCIENZA", "Vuoto – Vita – Vuoto. È la sequenza che si ripete."),
        ("IO", "Quella sera ero stato al McDonald’s."),
        ("IO", "Panino doppio cheeseburger. Cercavo di non strozzarmi."),
        ("IO", "Mi guardavo attorno. Scrutavo. Prendevo appunti nella mia testa."),
        ("COSCIENZA", "Gerarchie perfette, anche in un tempio del fast food."),
        ("IO", "Una ragazza bellissima, tatuata, si siede di fronte al mio tavolo."),
        ("COSCIENZA", "Desiderio che scatta come un impulso elettrico."),
        ("IO", "Perché abbiamo bisogno di amare? O di essere amati?"),
        ("COSCIENZA", "Forse solo per essere confermati: 'Tu esisti'."),
        ("IO", "Ma prima dell’esistenza? Vuoto."),
        ("COSCIENZA", "Solo silenzio. Solo buio. Solo attesa."),
    ]


# --------------------------------------------------------------------------------------
# Funzione per mostrare immagine finale con fade/glitch
# --------------------------------------------------------------------------------------
def mostra_finale(screen, screen_width, screen_height):
    img_path = asset("assets", "background", "scena2_pic.png")
    snd_path = asset("assets", "audio", "final_scena2.wav")

    if not os.path.exists(img_path):
        print("Immagine finale non trovata:", img_path)
        return

    # Carica immagine finale nitida
    final_img = pygame.image.load(img_path).convert()
    final_img = pygame.transform.scale(final_img, (screen_width, screen_height))

    # Suono finale
    if os.path.exists(snd_path):
        sound = pygame.mixer.Sound(snd_path)
        sound.play()

    # Fade out musica ambientale
    pygame.mixer.music.fadeout(3000)

    start_time = pygame.time.get_ticks()
    running_finale = True

    while running_finale:
        elapsed = (pygame.time.get_ticks() - start_time) / 1000.0
        screen.fill((0, 0, 0))

        if elapsed < 8:
            # Fase glitch/disturbo: l'immagine non è nitida
            scale_factor = random.uniform(0.9, 1.1)
            angle = random.randint(-3, 3)
            offset_x = random.randint(-15, 15)
            offset_y = random.randint(-15, 15)

            # Applico disturbo (scalatura + rotazione + offset)
            glitch_img = pygame.transform.rotozoom(final_img, angle, scale_factor)
            rect = glitch_img.get_rect(center=(screen_width // 2 + offset_x,
                                               screen_height // 2 + offset_y))
            screen.blit(glitch_img, rect)

        elif elapsed < 10:
            # Fase nitida con fade out nero
            screen.blit(final_img, (0, 0))

            fade_progress = (elapsed - 8.0) / 2.0  # 0 → 1 nell'intervallo 8s–10s
            fade_alpha = int(fade_progress * 255)

            fade_surface = pygame.Surface((screen_width, screen_height))
            fade_surface.fill((0, 0, 0))
            fade_surface.set_alpha(fade_alpha)
            screen.blit(fade_surface, (0, 0))

        else:
            running_finale = False

        pygame.display.flip()
        pygame.time.delay(40)  # ~25 fps per stabilità

    # Uscita dal gioco
    pygame.quit()
    os._exit(0)

# --------------------------------------------------------------------------------------
# Avvio Scena
# --------------------------------------------------------------------------------------
def avvia_scena(screen, clock):
    print("Avvio scena 2...")

    # ----------------------------------------------------------------------------------
    # Audio
    # ----------------------------------------------------------------------------------
    pygame.mixer.set_num_channels(16)
    CHANNEL_GLITCH = pygame.mixer.Channel(14)

    ambient_music_path = asset("assets", "audio", "s.wav")
    glitch_sound = pygame.mixer.Sound(asset("assets", "audio", "Glitch.ogg"))
    glitch_sound.set_volume(0.7)

    pygame.mixer.music.load(ambient_music_path)
    pygame.mixer.music.set_volume(0.3)
    pygame.mixer.music.play(-1)

    # ----------------------------------------------------------------------------------
    # Grafica
    # ----------------------------------------------------------------------------------
    screen_width, screen_height = screen.get_size()
    background_image = pygame.image.load(asset("assets", "background", "mac.png")).convert()
    background_image = pygame.transform.scale(background_image, (screen_width, screen_height))

    # ----------------------------------------------------------------------------------
    # Stato
    # ----------------------------------------------------------------------------------
    entity = EntityBrain("entity_model")
    entity_triggered = False
    entity_active = False
    entity_response = ""
    entity_timer = 0
    entity_alpha = 255

    dialog_manager = DialogManager(
        io_font_path=asset("assets", "fonts", "fragile.ttf"),
        coscienza_font_path=asset("assets", "fonts", "reflective.ttf"),
        entity_font_path=asset("assets", "fonts", "entity.ttf"),
        font_size=28
    )
    dialog_manager.load_dialog(get_scene())
    ENTITY_FONT = pygame.font.Font(asset("assets", "fonts", "entity.ttf"), 26)

    # ----------------------------------------------------------------------------------
    # Helpers
    # ----------------------------------------------------------------------------------
    def scrivi_blocco_note(testo: str) -> Path:
        try:
            desktop = Path(os.environ.get("USERPROFILE", "")) / "Desktop"
            if not desktop.exists():
                desktop = Path.home() / "Desktop"
        except Exception:
            desktop = Path.home() / "Desktop"

        file_path = desktop / "entita.txt"
        try:
            with open(file_path, "a", encoding="utf-8") as f:
                f.write((testo or "").strip() + "\n")
        except Exception as e:
            print("Errore scrittura file:", e)
        return file_path

    def render_text_with_outline(text, font, text_color, outline_color=(0, 0, 0)):
        base = font.render(text, True, text_color)
        outline = pygame.Surface((base.get_width() + 2, base.get_height() + 2), pygame.SRCALPHA)
        for dx in [-1, 0, 1]:
            for dy in [-1, 0, 1]:
                if dx != 0 or dy != 0:
                    outline.blit(font.render(text, True, outline_color), (1 + dx, 1 + dy))
        outline.blit(base, (1, 1))
        return outline

    def build_dialog_context() -> str:
        context_lines = []
        for line in dialog_manager.dialog_lines[: dialog_manager.current_line + 1]:
            if len(line) == 3:
                spk, prefix, txt = line
            elif len(line) == 2:
                spk, txt = line
                prefix = f"{spk}:"
            else:
                continue
            if prefix:
                context_lines.append(f"{prefix} {txt}")
            else:
                context_lines.append(txt)
        return "\n".join(context_lines)

    # ----------------------------------------------------------------------------------
    # Loop
    # ----------------------------------------------------------------------------------
    running = True
    while running:
        screen.blit(background_image, (0, 0))

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            if event.type == pygame.KEYDOWN and event.key == pygame.K_RETURN:
                # Fine scena → ENTITÀ risponde + immagine finale
                if dialog_manager.current_line == len(dialog_manager.dialog_lines) - 1 and not entity_triggered:
                    dialog_so_far = build_dialog_context()
                    risposta_entita = entity.generate_response(f"{dialog_so_far}\nENTITÀ:")

                    if risposta_entita:
                        CHANNEL_GLITCH.play(glitch_sound)
                        scrivi_blocco_note(risposta_entita)
                        dialog_manager.dialog_lines.append(("ENTITÀ", risposta_entita))
                        entity_active = True
                        entity_response = risposta_entita
                        entity_timer = pygame.time.get_ticks()
                        entity_alpha = 255

                    entity_triggered = True
                    mostra_finale(screen, screen_width, screen_height)

                else:
                    dialog_manager.next_line()

                    # ENTITÀ interviene casualmente
                    if dialog_manager.current_line > 0:
                        if random.random() < 0.3:
                            dialog_so_far = build_dialog_context()
                            risposta = entity.generate_response(f"{dialog_so_far}\nENTITÀ:")
                            if risposta:
                                CHANNEL_GLITCH.play(glitch_sound)
                                scrivi_blocco_note(risposta)
                                entity_active = True
                                entity_response = risposta
                                entity_timer = pygame.time.get_ticks()
                                entity_alpha = 255

        # Disegna UI dialoghi
        dialog_manager.draw(screen)

        # Disegna ENTITÀ
        if entity_active:
            elapsed = pygame.time.get_ticks() - entity_timer
            full_text = "ENTITÀ: " + entity_response.strip().capitalize()
            text_surface = render_text_with_outline(full_text, ENTITY_FONT, (255, 55, 55))
            text_surface.set_alpha(entity_alpha)
            text_rect = text_surface.get_rect(center=(screen_width // 2, screen_height // 2 - 100))
            screen.blit(text_surface, text_rect)

            if elapsed > 3000:
                entity_alpha -= 3
                if entity_alpha <= 0:
                    entity_active = False
                    entity_response = ""

        pygame.display.flip()
        clock.tick(30)

    pygame.quit()
