import pygame
import sys
import random
import subprocess
import os
import time
from pathlib import Path
from scenes.scene1 import get_scene
from engine.dialog_manager import DialogManager
from engine.entity_brain import EntityBrain

print("Avvio gioco...")

# Inizializzazione
pygame.init()
pygame.mixer.init()

# Audio ambientale
pygame.mixer.music.load("assets/audio/Ambient.ogg")
pygame.mixer.music.set_volume(0.5)
pygame.mixer.music.play(-1)

# Suono glitch da usare quando parla l'entità
glitch_sound = pygame.mixer.Sound("assets/audio/Glitch.ogg")
glitch_sound.set_volume(0.7)

screen_width, screen_height = 1280, 720
screen = pygame.display.set_mode((screen_width, screen_height))
pygame.display.set_caption("Dialoghi con un’Eco")
clock = pygame.time.Clock()

# Sfondo
background_image = pygame.image.load("assets/background/room.png").convert()
background_image = pygame.transform.scale(background_image, (screen_width, screen_height))

# Entità intelligente
entity = EntityBrain("entity_model")
entity_triggered = False
entity_active = False
entity_response = ""
entity_timer = 0
entity_alpha = 255

# Inizializza gestore dialoghi
dialog_manager = DialogManager(
    io_font_path="assets/fonts/fragile.ttf",
    coscienza_font_path="assets/fonts/reflective.ttf",
    entity_font_path="assets/fonts/entity.ttf",
    font_size=28
)

# Carica scena iniziale
dialog_manager.load_dialog(get_scene())

def riproduci_suono_finale():
    try:
        mp3_path = os.path.abspath("assets/audio/Ti_Vedo.ogg")
        os.startfile(mp3_path) 
    except Exception as e:
        print("Errore nella riproduzione del suono finale:", e)


# Funzioni blocco note
def scrivi_blocco_note(testo):
    desktop = Path(os.path.join(os.environ["USERPROFILE"], "Desktop"))
    file_path = desktop / "entita.txt"
    try:
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(testo.strip() + "\n\nTI VEDO")
    except Exception as e:
        print("Errore scrittura file:", e)
    return file_path

def apri_blocco_note(path):
    inizio = time.time()
    while not path.exists():
        if time.time() - inizio > 2:
            print("Timeout: il file non è stato creato.")
            return
        time.sleep(0.1)
    try:
        os.startfile(str(path))
    except Exception as e:
        print("Errore apertura blocco note:", e)

# Funzione log entità
def log_entita_response(risposta):
    if not risposta:
        return
    try:
        desktop = Path(os.path.join(os.environ["USERPROFILE"], "Desktop"))
        log_path = desktop / "log_entita.txt"
        with open(log_path, "a", encoding="utf-8") as logf:
            timestamp = pygame.time.get_ticks() / 1000.0
            logf.write(f"[{timestamp:.2f}s] ENTITÀ: {risposta}\n")
    except Exception as e:
        print("Errore salvataggio log:", e)

# Funzione per rendere testo con bordo nero
def render_text_with_outline(text, font, text_color, outline_color=(0, 0, 0)):
    base = font.render(text, True, text_color)
    outline = pygame.Surface((base.get_width() + 2, base.get_height() + 2), pygame.SRCALPHA)
    for dx in [-1, 0, 1]:
        for dy in [-1, 0, 1]:
            if dx != 0 or dy != 0:
                outline.blit(font.render(text, True, outline_color), (1 + dx, 1 + dy))
    outline.blit(base, (1, 1))
    return outline

# Loop principale
running = True
while running:
    screen.blit(background_image, (0, 0))

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

        if event.type == pygame.KEYDOWN and event.key == pygame.K_RETURN:
            if dialog_manager.current_line == len(dialog_manager.dialog_lines) - 1 and not entity_triggered:
                prompt = "IO: O forse solo rotto.\nENTITÀ:"
                risposta_entita = entity.generate_response(prompt)

                if risposta_entita:
                    glitch_sound.play()
                    log_entita_response(risposta_entita)
                    dialog_manager.dialog_lines.append(("ENTITÀ", risposta_entita))
                    dialog_manager.dialog_lines.append(("ENTITÀ", "TI VEDO"))
                    riproduci_suono_finale()
                    entity_active = True
                    entity_response = risposta_entita
                    entity_timer = pygame.time.get_ticks()
                    entity_alpha = 255
                else:
                    risposta_entita = "..."

                

                file_path = scrivi_blocco_note(risposta_entita)
                pygame.display.flip()
                pygame.time.delay(100)
                apri_blocco_note(file_path)
                entity_triggered = True

            else:
                dialog_manager.next_line()

                if dialog_manager.current_line > 0:
                    speaker, prefix, text = dialog_manager.dialog_lines[dialog_manager.current_line - 1]
                    if speaker == "IO" and not entity_active and random.random() < 0.3:
                        prompt = f"{text}\nENTITÀ:"
                        risposta = entity.generate_response(prompt)

                        if risposta:
                            glitch_sound.play()
                            log_entita_response(risposta)
                            entity_active = True
                            entity_response = risposta
                            entity_timer = pygame.time.get_ticks()
                            entity_alpha = 255

    dialog_manager.draw(screen)

    if entity_active:
        elapsed = pygame.time.get_ticks() - entity_timer
        entity_font = pygame.font.Font("assets/fonts/entity.ttf", 26)
        full_text = "ENTITÀ: " + entity_response.strip().capitalize()
        text_surface = render_text_with_outline(full_text, entity_font, (255, 55, 55))
        text_surface.set_alpha(entity_alpha)
        text_rect = text_surface.get_rect(center=(screen_width // 2, screen_height // 2 - 100))
        screen.blit(text_surface, text_rect)

        if elapsed > 3000:
            entity_alpha -= 3
            if entity_alpha <= 0:
                entity_alpha = 0
                entity_active = False
                entity_response = ""

    pygame.display.flip()
    clock.tick(30)

pygame.quit()
sys.exit()
