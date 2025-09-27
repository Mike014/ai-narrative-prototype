# scenes/Volume1/scene1_diary_breaks.py
# -*- coding: utf-8 -*-
import os
import time
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
    return start  # fallback (meglio di niente)

THIS_FILE = Path(__file__).resolve()
BASE_DIR = find_project_root(THIS_FILE)
ASSETS_DIR = BASE_DIR / "assets"

def asset_path(*parts) -> str:
    return str(ASSETS_DIR.joinpath(*parts))

# -----------------------------------------------------------------------------
# Scena 1: "The Diary Breaks"
# -----------------------------------------------------------------------------
def get_scene():
    return [
        ("IO", "La stanza era vuota."),
        ("IO", "O forse troppo piena."),
        ("COSCIENZA", "Strano come la mente riempia ciò che manca."),
        ("IO", "Roba sparsa ovunque, memoria a pezzi."),
        ("IO", "Il ventilatore mi puntava addosso come un interrogatorio."),
        ("COSCIENZA", "Forse cercava risposte."),
        ("IO", "Colonne sonore malinconiche scorrevano..."),
        ("IO", "Sensibili come i loro protagonisti."),
        ("IO", "Il collo rigido, la cervicale graffiava."),
        ("IO", "Il lampadario oscillava appena, quasi chiedendo scusa per esistere."),
        ("IO", "Una Monster già a metà, le Highlander digerite male."),
        ("IO", "In call, con nessuno."),
        ("IO", "Lui era morto."),
        ("IO", "Io non mi fidavo più di nessuno."),
        ("COSCIENZA", "Eppure stai parlando con me."),
        ("IO", "Paranoia costante, allarme sempre attivo."),
        ("IO", "Mi chiedevo: com'è che la Routine rende sacra la vita di qualcuno?"),
        ("COSCIENZA", "Perché l'abitudine è l’unico dio che non delude."),
        ("IO", "Lo stesso caffè... lo stesso espresso macchiato freddo..."),
        ("IO", "Nel solito bicchiere di vetro. La stessa acqua."),
        ("IO", "Ma se un giorno, per sbaglio... ti verso la naturale al posto della frizzante?"),
        ("COSCIENZA", "Crash."),
        ("IO", "Come un virus nel sistema. La macchina si sveglia."),
        ("IO", "L’avevo chiesta frizzante."),
        ("IO", "Non era successo ieri. Ma oggi sì."),
        ("COSCIENZA", "Nel microscopico scarto... l’umano si ricorda di essere sveglio."),
        ("IO", "O forse solo rotto."),
    ]

# -----------------------------------------------------------------------------
# Helpers generici
# -----------------------------------------------------------------------------
def open_path_crossplatform(path: Path):
    try:
        system = platform.system()
        if system == "Windows":
            os.startfile(str(path))  # type: ignore[attr-defined]
        elif system == "Darwin":
            subprocess.Popen(["open", str(path)])
        else:
            subprocess.Popen(["xdg-open", str(path)])
    except Exception as e:
        print("Impossibile aprire il file:", e)

def scrivi_blocco_note(testo: str) -> Path:
    try:
        desktop = Path(os.environ.get("USERPROFILE", "")) / "Desktop"
        if not desktop.exists():
            desktop = Path.home() / "Desktop"
    except Exception:
        desktop = Path.home() / "Desktop"

    file_path = desktop / "ENTITA'.txt"
    try:
        with open(file_path, "w", encoding="utf-8") as f:
            f.write((testo or "").strip() + "\n\nTI VEDO")
    except Exception as e:
        print("Errore scrittura file:", e)
    return file_path

def apri_blocco_note(path: Path):
    start = time.time()
    while not path.exists():
        if time.time() - start > 2:
            print("Timeout: il file non è stato creato.")
            return
        time.sleep(0.05)
    open_path_crossplatform(path)

def log_entita_response(risposta: str):
    if not risposta:
        return
    try:
        desktop = Path(os.environ.get("USERPROFILE", "")) / "Desktop"
        if not desktop.exists():
            desktop = Path.home() / "Desktop"
        log_path = desktop / "log_entita.txt"
        with open(log_path, "a", encoding="utf-8") as logf:
            timestamp = pygame.time.get_ticks() / 1000.0
            logf.write(f"[{timestamp:.2f}s] ENTITÀ: {risposta}\n")
    except Exception as e:
        print("Errore salvataggio log:", e)

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
        ("background", "scene1_background.jpg"),  # se mai lo aggiungi
        ("background", "room.png"),               # ESISTE nella tua repo
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
    CHANNEL_TIVEDO = pygame.mixer.Channel(15)

    # Audio
    ambient_music_path = asset_path("audio", "Ambient.ogg")
    glitch_path = asset_path("audio", "Glitch.ogg")
    ti_vedo_path = asset_path("audio", "Ti_Vedo.ogg")

    pygame.mixer.music.load(ambient_music_path)
    pygame.mixer.music.set_volume(0.5)
    pygame.mixer.music.play(-1)

    glitch_sound = pygame.mixer.Sound(glitch_path)
    glitch_sound.set_volume(0.7)

    ti_vedo_sfx = pygame.mixer.Sound(ti_vedo_path)
    ti_vedo_sfx.set_volume(1.0)

    # Background
    background_image, chosen_bg = load_background(screen)
    print(f"[DEBUG] Background: {chosen_bg}")

    # Font reali presenti
    io_font_path = ASSETS_DIR / "fonts" / "fragile.ttf"
    cosc_font_path = ASSETS_DIR / "fonts" / "reflective.ttf"
    entity_font_path = ASSETS_DIR / "fonts" / "entity.ttf"

    # Dialog Manager
    dialog_manager = DialogManager(
        io_font_path=str(io_font_path),
        coscienza_font_path=str(cosc_font_path),
        entity_font_path=str(entity_font_path),
        font_size=28
    )
    dialog_manager.load_dialog(get_scene())

    # Font overlay ENTITÀ
    ENTITY_FONT = pygame.font.Font(str(entity_font_path), 26)

    # Stato ENTITÀ
    entity = EntityBrain("entity_model")
    entity_triggered = False
    entity_active = False
    entity_response = ""
    entity_timer = 0
    entity_alpha = 255

    # Helper suono finale (resta identico)
    def riproduci_suono_finale():
        try:
            CHANNEL_TIVEDO.stop()
            CHANNEL_TIVEDO.set_volume(1.0)
            CHANNEL_TIVEDO.play(ti_vedo_sfx)
            if CHANNEL_TIVEDO.get_busy():
                return True

            ch = pygame.mixer.find_channel(force=True)
            if ch is not None:
                ch.stop()
                ch.set_volume(1.0)
                ch.play(ti_vedo_sfx)
                if ch.get_busy():
                    return True

            if platform.system() == "Windows":
                try:
                    import winsound
                    winsound.PlaySound(str(Path(ti_vedo_path).resolve()),
                                       winsound.SND_FILENAME | winsound.SND_ASYNC)
                    return True
                except Exception:
                    pass

            abs_path = str(Path(ti_vedo_path).resolve())
            try:
                if platform.system() == "Windows":
                    os.startfile(abs_path)  # type: ignore[attr-defined]
                elif platform.system() == "Darwin":
                    subprocess.Popen(["open", abs_path])
                else:
                    subprocess.Popen(["xdg-open", abs_path])
                return True
            except Exception as e2:
                print("Fallback player di sistema fallito:", e2)
                return False

        except Exception as e:
            print("Errore nella riproduzione TI_VEDO:", e)
            try:
                abs_path = str(Path(ti_vedo_path).resolve())
                if platform.system() == "Windows":
                    os.startfile(abs_path)  # type: ignore[attr-defined]
                elif platform.system() == "Darwin":
                    subprocess.Popen(["open", abs_path])
                else:
                    subprocess.Popen(["xdg-open", abs_path])
                return True
            except Exception:
                return False

    # Loop principale
    running = True
    while running:
        screen.blit(background_image, (0, 0))

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            if event.type == pygame.KEYDOWN and event.key == pygame.K_RETURN:
                # Invio: o trigger finale o next line
                last_idx = len(dialog_manager.dialog_lines) - 1
                if dialog_manager.current_line == last_idx and not entity_triggered:
                    prompt = "IO: O forse solo rotto.\nENTITÀ:"
                    risposta_entita = entity.generate_response(prompt) or "..."
                    CHANNEL_GLITCH.play(glitch_sound)
                    log_entita_response(risposta_entita)

                    dialog_manager.dialog_lines.append(("ENTITÀ", risposta_entita))
                    dialog_manager.dialog_lines.append(("ENTITÀ", "TI VEDO"))

                    entity_active = True
                    entity_response = risposta_entita
                    entity_timer = pygame.time.get_ticks()
                    entity_alpha = 255

                    riproduci_suono_finale()
                    file_path = scrivi_blocco_note(risposta_entita)
                    apri_blocco_note(file_path)
                    entity_triggered = True
                else:
                    dialog_manager.next_line()

                    # Intervento casuale ENTITÀ su battute di IO
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
                                log_entita_response(risposta)
                                entity_active = True
                                entity_response = risposta
                                entity_timer = pygame.time.get_ticks()
                                entity_alpha = 255

        # Disegno dialoghi
        dialog_manager.draw(screen)

        # Overlay ENTITÀ con fade-out
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

        pygame.display.flip()
        clock.tick(30)

    pygame.quit()
