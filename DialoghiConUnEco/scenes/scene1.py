# scenes/scene1.py
# -*- coding: utf-8 -*-

import os
import time
import random
import platform
import subprocess
from pathlib import Path

import pygame

from engine.dialog_manager import DialogManager   # Gestisce il testo a schermo e l’avanzamento del dialogo
from engine.entity_brain import EntityBrain       # Modello/generatore di risposte dell'ENTITÀ


# --------------------------------------------------------------------------------------
# Impostazione percorsi robusti rispetto alla working directory
# scene1.py si trova in: <project_root>/scenes/scene1.py  -> parents[1] = <project_root>
# --------------------------------------------------------------------------------------
BASE_DIR = Path(__file__).resolve().parents[1]


def asset(*parts) -> str:
    """Costruisce un path assoluto a partire dalla radice del progetto."""
    return str(BASE_DIR.joinpath(*parts))


# --------------------------------------------------------------------------------------
# Scena 1: "La stanza. Il crash."
# --------------------------------------------------------------------------------------
def get_scene():
    """Lista di battute (speaker, testo) che compongono la scena iniziale."""
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


def avvia_scena(screen, clock):
    """
    Esegue la scena 1:
    - carica musica d'ambiente e suoni glitch
    - mostra sfondo e dialoghi con outline
    - innesca l'ENTITÀ alla fine della scena o casualmente su alcune battute di "IO"
    - logga le risposte dell'ENTITÀ e scrive un file sul desktop
    - sfuma il testo dell'ENTITÀ dopo la comparsa
    - suono finale forzato (senza ducking): Pygame channel -> canale forzato -> winsound -> player di sistema
    """
    print("Avvio scena 1...")

    # ----------------------------------------------------------------------------------
    # Audio: mixer e canali dedicati
    # ----------------------------------------------------------------------------------
    pygame.mixer.set_num_channels(16)
    CHANNEL_GLITCH = pygame.mixer.Channel(14)   # canale riservato al glitch
    CHANNEL_TIVEDO = pygame.mixer.Channel(15)   # canale riservato al suono finale

    # Percorsi
    ambient_music_path = asset("assets", "audio", "Ambient.ogg")
    ti_vedo_path = asset("assets", "audio", "Ti_Vedo.wav")  # consigliato WAV 48k

    # Musica d'ambiente
    pygame.mixer.music.load(ambient_music_path)
    pygame.mixer.music.set_volume(0.5)
    pygame.mixer.music.play(-1)  # loop infinito

    # SFX
    glitch_sound = pygame.mixer.Sound(asset("assets", "audio", "Glitch.ogg"))
    glitch_sound.set_volume(0.7)

    ti_vedo_sfx = pygame.mixer.Sound(ti_vedo_path)
    ti_vedo_sfx.set_volume(1.0)

    # ----------------------------------------------------------------------------------
    # Grafica di base (sfondo)
    # ----------------------------------------------------------------------------------
    screen_width, screen_height = screen.get_size()
    background_image = pygame.image.load(asset("assets", "background", "room.png")).convert()
    background_image = pygame.transform.scale(background_image, (screen_width, screen_height))

    # ----------------------------------------------------------------------------------
    # Stato e componenti di scena
    # ----------------------------------------------------------------------------------
    entity = EntityBrain("entity_model")   # backend generativo dell’ENTITÀ
    entity_triggered = False               # True dopo il trigger finale (chiusura scena)
    entity_active = False                  # True quando il box ENTITÀ è visibile
    entity_response = ""                   # testo mostrato dall’ENTITÀ
    entity_timer = 0                       # timestamp di apparizione per la sfumatura
    entity_alpha = 255                     # trasparenza del testo ENTITÀ (per fade-out)

    dialog_manager = DialogManager(
        io_font_path=asset("assets", "fonts", "fragile.ttf"),
        coscienza_font_path=asset("assets", "fonts", "reflective.ttf"),
        entity_font_path=asset("assets", "fonts", "entity.ttf"),
        font_size=28
    )
    dialog_manager.load_dialog(get_scene())

    ENTITY_FONT = pygame.font.Font(asset("assets", "fonts", "entity.ttf"), 26)

    # ----------------------------------------------------------------------------------
    # Helper: apertura file cross-platform
    # ----------------------------------------------------------------------------------
    def open_path_crossplatform(path: Path):
        try:
            system = platform.system()
            if system == "Windows":
                os.startfile(str(path))            # type: ignore[attr-defined]
            elif system == "Darwin":               # macOS
                subprocess.Popen(["open", str(path)])
            else:                                  # Linux, *BSD
                subprocess.Popen(["xdg-open", str(path)])
        except Exception as e:
            print("Impossibile aprire il file:", e)

    # ----------------------------------------------------------------------------------
    # Helper: scrittura file sul Desktop
    # ----------------------------------------------------------------------------------
    def scrivi_blocco_note(testo: str) -> Path:
        """Scrive 'entita.txt' sul Desktop con la risposta dell’ENTITÀ + firma 'TI VEDO'."""
        try:
            desktop = Path(os.environ.get("USERPROFILE", "")) / "Desktop"
            if not desktop.exists():
                desktop = Path.home() / "Desktop"
        except Exception:
            desktop = Path.home() / "Desktop"

        file_path = desktop / "entita.txt"
        try:
            with open(file_path, "w", encoding="utf-8") as f:
                f.write((testo or "").strip() + "\n\nTI VEDO")
        except Exception as e:
            print("Errore scrittura file:", e)
        return file_path

    def apri_blocco_note(path: Path):
        """Attende la creazione del file (max 2s) e poi lo apre con l’app di default."""
        start = time.time()
        while not path.exists():
            if time.time() - start > 2:
                print("Timeout: il file non è stato creato.")
                return
            time.sleep(0.05)
        open_path_crossplatform(path)

    # ----------------------------------------------------------------------------------
    # Helper: logging risposte ENTITÀ
    # ----------------------------------------------------------------------------------
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

    # ----------------------------------------------------------------------------------
    # Helper: render testo con bordo (outline)
    # ----------------------------------------------------------------------------------
    def render_text_with_outline(text, font, text_color, outline_color=(0, 0, 0)):
        base = font.render(text, True, text_color)
        outline = pygame.Surface((base.get_width() + 2, base.get_height() + 2), pygame.SRCALPHA)
        for dx in [-1, 0, 1]:
            for dy in [-1, 0, 1]:
                if dx != 0 or dy != 0:
                    outline.blit(font.render(text, True, outline_color), (1 + dx, 1 + dy))
        outline.blit(base, (1, 1))
        return outline

    # ----------------------------------------------------------------------------------
    # Helper: forza riproduzione suono finale (senza ducking)
    # ----------------------------------------------------------------------------------
    def riproduci_suono_finale():
        """
        Forza la riproduzione di TI_VEDO:
        1) Canale dedicato Pygame
        2) Canale forzato Pygame
        3) winsound (Windows, WAV)
        4) Player di sistema (open/xdg-open/os.startfile)
        """
        try:
            # 1) Canale dedicato
            CHANNEL_TIVEDO.stop()
            CHANNEL_TIVEDO.set_volume(1.0)
            CHANNEL_TIVEDO.play(ti_vedo_sfx)
            if CHANNEL_TIVEDO.get_busy():
                return True

            # 2) Canale forzato
            ch = pygame.mixer.find_channel(force=True)
            if ch is not None:
                ch.stop()
                ch.set_volume(1.0)
                ch.play(ti_vedo_sfx)
                if ch.get_busy():
                    return True

            # 3) winsound (Windows, richiede WAV)
            if platform.system() == "Windows":
                try:
                    import winsound
                    winsound.PlaySound(str(Path(ti_vedo_path).resolve()),
                                       winsound.SND_FILENAME | winsound.SND_ASYNC)
                    return True
                except Exception:
                    pass

            # 4) Player di sistema
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
            # Ultimo tentativo: player di sistema
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

    # ----------------------------------------------------------------------------------
    # Loop principale della scena
    # ----------------------------------------------------------------------------------
    running = True
    while running:
        # Disegna sfondo
        screen.blit(background_image, (0, 0))

        # Eventi
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            if event.type == pygame.KEYDOWN and event.key == pygame.K_RETURN:
                # Invio: avanza o trigger finale
                if dialog_manager.current_line == len(dialog_manager.dialog_lines) - 1 and not entity_triggered:
                    # Trigger finale: risposta dell’ENTITÀ
                    prompt = "IO: O forse solo rotto.\nENTITÀ:"
                    risposta_entita = entity.generate_response(prompt)

                    if risposta_entita:
                        CHANNEL_GLITCH.play(glitch_sound)
                        log_entita_response(risposta_entita)

                        # Mostra anche nel flusso di dialogo
                        dialog_manager.dialog_lines.append(("ENTITÀ", risposta_entita))
                        dialog_manager.dialog_lines.append(("ENTITÀ", "TI VEDO"))

                        # Sovraimpressione ENTITÀ
                        entity_active = True
                        entity_response = risposta_entita
                        entity_timer = pygame.time.get_ticks()
                        entity_alpha = 255
                    else:
                        risposta_entita = "..."

                    # Suono finale: forzato sempre
                    riproduci_suono_finale()

                    # File sul Desktop + apertura
                    file_path = scrivi_blocco_note(risposta_entita)
                    apri_blocco_note(file_path)

                    # Evita doppi trigger
                    entity_triggered = True

                else:
                    # Avanza la battuta
                    dialog_manager.next_line()

                    # Intervento casuale dell’ENTITÀ su battute di "IO"
                    if dialog_manager.current_line > 0:
                        last_line = dialog_manager.dialog_lines[dialog_manager.current_line - 1]
                        # Unpack robusto (supporta 2-tuple o 3+)
                        if isinstance(last_line, (list, tuple)):
                            if len(last_line) == 2:
                                speaker, text = last_line
                            elif len(last_line) >= 3:
                                speaker, text = last_line[0], last_line[-1]
                            else:
                                speaker, text = None, ""
                        else:
                            speaker, text = None, ""

                        if speaker == "IO" and not entity_active and random.random() < 0.3:
                            prompt = f"{text}\nENTITÀ:"
                            risposta = entity.generate_response(prompt)
                            if risposta:
                                CHANNEL_GLITCH.play(glitch_sound)
                                log_entita_response(risposta)
                                entity_active = True
                                entity_response = risposta
                                entity_timer = pygame.time.get_ticks()
                                entity_alpha = 255

        # Disegna UI dialoghi
        dialog_manager.draw(screen)

        # Sovraimpressione ENTITÀ (fade-out)
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
                    entity_alpha = 0
                    entity_active = False
                    entity_response = ""

        # Presentazione frame
        pygame.display.flip()
        clock.tick(30)

    # Uscita dalla scena: la chiusura generale va gestita nel main.
    pygame.quit()
