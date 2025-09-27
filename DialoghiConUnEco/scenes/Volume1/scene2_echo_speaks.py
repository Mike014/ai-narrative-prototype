# scenes/Volume1/scene2_echo_speaks.py
# -*- coding: utf-8 -*-

import os
import random
import platform
import subprocess
from pathlib import Path

import pygame
from dotenv import load_dotenv

from engine.dialog_manager import DialogManager
from engine.entity_brain import EntityBrain

# -----------------------------------------------------------------------------
# Env (per eventuali API key usate da EntityBrain)
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
    """assets/... → string path"""
    return str(ASSETS_DIR.joinpath(*parts))

# -----------------------------------------------------------------------------
# Scene content
# -----------------------------------------------------------------------------
def get_scene():
    return [
        ("IO", "Poche ore al mio compleanno."),
        ("IO", "L'attesa prima della celebrazione della propria nascita."),
        ("IO", "Mi sono sempre chiesto: scatta a mezzanotte,"),
        ("IO", "o nel momento preciso in cui hai aperto gli occhi,"),
        ("IO", "respirato aria con polmoni nuovi,"),
        ("IO", "sentito sulla pelle quelle piccole molecole pruriginose che ti dicono che sei vivo?"),
        ("COSCIENZA", "Il primo respiro marca l'inizio, non l'orologio."),
        
        ("IO", "Quella sensazione di 'accensione'. Click."),
        ("IO", "Sistema operativo: installato."),
        ("COSCIENZA", "Un boot che nessuno ricorda, ma tutti hanno fatto."),
        
        ("IO", "E prima? Cosa c'era?"),
        ("IO", "Qualcosa di simile alla morte?"),
        ("IO", "Una stanza totalmente buia, vuota, senza eco."),
        ("COSCIENZA", "Vuoto – Vita – Vuoto. È la sequenza che si ripete."),
        
        ("IO", "Quella sera ero stato al McDonald's."),
        ("IO", "Panino doppio cheeseburger. Cercavo di non strozzarmi."),
        ("IO", "Mi guardavo attorno. Scrutavo. Prendevo appunti nella mia testa."),
        ("COSCIENZA", "Osservi gerarchie perfette, anche in un tempio del fast food."),
        
        ("IO", "I ranghi degli operai: tizi in fondo alla sala,"),
        ("IO", "preparazione vassoi, grembiule, berretto per la forfora, guanti in lattice."),
        ("IO", "Verso il centro aumentano i ranghi."),
        ("IO", "Tipi con le cuffie, gestiscono le preparazioni, smistano panini."),
        ("COSCIENZA", "Ogni livello ha i suoi simboli di potere."),
        
        ("IO", "Poi i tizi in camicia blu: servono vassoi, prendono pagamenti."),
        ("IO", "E poi ancora più su: tipi brizzolati, camicia chiara,"),
        ("IO", "controllano che il cassetto abbia tutte le cannucce, in ordine di lunghezza."),
        ("COSCIENZA", "Ordine che maschera il caos dell'esistenza."),
        
        ("IO", "Mi fermai. Sorso di Sprite."),
        ("IO", "Il buttafuori impassibile."),
        ("IO", "Una bambina al centro della sala, mani in su, si volta, cerca la mamma."),
        ("COSCIENZA", "Innocenza che cerca connessione nel vuoto."),
        
        ("IO", "Una ragazza bellissima, tatuata, si siede di fronte al mio tavolo."),
        ("IO", "Rossa. Sguardo sensuale."),
        ("IO", "Per un attimo, volevo chiederle di passare la notte con me."),
        ("COSCIENZA", "Desiderio che accende senza preavviso."),
        
        ("IO", "Desisto. Aveva una pancetta che fuoriusciva quando si sedeva."),
        ("IO", "Non mi piaceva quel dettaglio. O forse sì, ma avevo paura."),
        ("COSCIENZA", "La perfezione immaginata scontra con la realtà umana."),
        
        ("IO", "Una coppia di coppie. Ordinano insieme. Non si staccano."),
        ("IO", "Una delle due: lui grasso, lei magra, occhiali."),
        ("IO", "Sicuramente nerd. Ama Sailor Moon, manga e Marvel."),
        ("IO", "Si dicono cose. Intrecciano i nasi."),
        ("COSCIENZA", "Intimità che disturba chi ne è escluso."),
        
        ("IO", "Mi copro la vista, come davanti a una scena di un film horror."),
        ("COSCIENZA", "L'amore altrui può essere tortura per chi è solo."),
        
        ("IO", "Poi smettono. La stanza torna al ritmo precedente:"),
        ("IO", "Tap, tap, tap, tap. 120 BPM."),
        ("IO", "Forse è il panino. O i cinque caffè al lavoro."),
        ("COSCIENZA", "Il battito del mondo che continua, indifferente."),
        
        ("IO", "Mi alzo. Fuori, tizi loschi, di fronte a un cumulo di Peroni."),
        ("IO", "Un gruppo di ragazze passa. Una di loro, stupenda."),
        ("IO", "Evito di guardarla. Ad alta voce, dico: 'Smettila.'"),
        ("COSCIENZA", "Parli a te stesso come a un cane randagio."),
        
        ("IO", "Mi fermo. Penso."),
        ("IO", "Perché abbiamo bisogno di amare? O di essere amati?"),
        ("COSCIENZA", "Forse è il desiderio di essere confermati: 'Tu esisti, e ti amo perché esisti.'"),
        
        ("IO", "Ma prima dell'esistenza? Vuoto."),
        ("IO", "Lì non esiste l'amore. Non esistiamo noi."),
        ("IO", "Niente da amare. Niente da essere."),
        ("COSCIENZA", "Solo silenzio. Solo buio. Solo attesa."),
        ("COSCIENZA", "E forse è lì che torniamo quando smettiamo di cercare.")
    ]

# -----------------------------------------------------------------------------
# Helpers
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

def scrivi_blocco_note(testo: str) -> Path:
    """Append su Desktop/log 'entita.txt' la risposta dell’ENTITÀ."""
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

def build_dialog_context(dialog_manager) -> str:
    """Concatena le battute fin qui mostrate in un contesto da dare all’ENTITÀ."""
    context_lines = []
    for line in dialog_manager.dialog_lines[: dialog_manager.current_line + 1]:
        if isinstance(line, (list, tuple)):
            if len(line) == 2:
                spk, txt = line
                context_lines.append(f"{spk}: {txt}")
            elif len(line) >= 3:
                spk, txt = line[0], line[-1]
                context_lines.append(f"{spk}: {txt}")
    return "\n".join(context_lines)

def load_background(screen):
    """Carica uno sfondo valido con fallback."""
    candidates = [
        ("background", "mac.png"),
        ("background", "room.png"),
    ]
    for parts in candidates:
        p = ASSETS_DIR.joinpath(*parts)
        if p.exists():
            img = pygame.image.load(str(p)).convert()
            return pygame.transform.scale(img, screen.get_size()), str(p)
    surf = pygame.Surface(screen.get_size())
    surf.fill((0, 0, 0))
    return surf, "(fill black)"

def mostra_finale(screen, screen_width, screen_height):
    """Glitch → nitido → fade nero, più audio finale."""
    img_path = asset_path("background", "scena2_pic.png")
    snd_path = asset_path("audio", "final_scena2.wav")

    if not os.path.exists(img_path):
        print("Immagine finale non trovata:", img_path)
        return

    final_img = pygame.image.load(img_path).convert()
    final_img = pygame.transform.scale(final_img, (screen_width, screen_height))

    if os.path.exists(snd_path):
        try:
            sound = pygame.mixer.Sound(snd_path)
            sound.play()
        except Exception as e:
            print("Errore riproduzione audio finale:", e)

    pygame.mixer.music.fadeout(3000)

    start_ticks = pygame.time.get_ticks()
    running_finale = True
    while running_finale:
        elapsed = (pygame.time.get_ticks() - start_ticks) / 1000.0
        screen.fill((0, 0, 0))

        if elapsed < 8.0:
            scale_factor = random.uniform(0.9, 1.1)
            angle = random.randint(-3, 3)
            offset_x = random.randint(-15, 15)
            offset_y = random.randint(-15, 15)
            glitch_img = pygame.transform.rotozoom(final_img, angle, scale_factor)
            rect = glitch_img.get_rect(center=(screen_width // 2 + offset_x,
                                               screen_height // 2 + offset_y))
            screen.blit(glitch_img, rect)
        elif elapsed < 10.0:
            screen.blit(final_img, (0, 0))
            fade_progress = (elapsed - 8.0) / 2.0
            fade_alpha = int(max(0.0, min(1.0, fade_progress)) * 255)
            fade_surface = pygame.Surface((screen_width, screen_height))
            fade_surface.fill((0, 0, 0))
            fade_surface.set_alpha(fade_alpha)
            screen.blit(fade_surface, (0, 0))
        else:
            running_finale = False

        pygame.display.flip()
        pygame.time.delay(40)  # ~25 fps

# -----------------------------------------------------------------------------
# Entry point scena
# -----------------------------------------------------------------------------
def avvia_scena(screen, clock):
    print(f"[DEBUG][SCENA2] BASE_DIR: {BASE_DIR}")
    print(f"[DEBUG][SCENA2] ASSETS_DIR: {ASSETS_DIR}")

    # Mixer
    pygame.mixer.set_num_channels(16)
    CHANNEL_GLITCH = pygame.mixer.Channel(14)

    # Audio (ambient + glitch)
    ambient_music_path = asset_path("audio", "s.wav")          # esiste
    glitch_path = asset_path("audio", "Glitch.ogg")            # esiste

    pygame.mixer.music.load(ambient_music_path)
    pygame.mixer.music.set_volume(0.3)
    pygame.mixer.music.play(-1)

    glitch_sound = pygame.mixer.Sound(glitch_path)
    glitch_sound.set_volume(0.7)

    # Background
    background_image, chosen_bg = load_background(screen)
    print(f"[DEBUG][SCENA2] Background: {chosen_bg}")

    # Font (tutti presenti in assets/fonts/)
    io_font_path      = ASSETS_DIR / "fonts" / "fragile.ttf"
    cosc_font_path    = ASSETS_DIR / "fonts" / "reflective.ttf"
    entity_font_path  = ASSETS_DIR / "fonts" / "entity.ttf"

    dialog_manager = DialogManager(
        io_font_path=str(io_font_path),
        coscienza_font_path=str(cosc_font_path),
        entity_font_path=str(entity_font_path),
        font_size=28
    )
    dialog_manager.load_dialog(get_scene())

    ENTITY_FONT = pygame.font.Font(str(entity_font_path), 26)

    # Stato ENTITÀ
    entity = EntityBrain("entity_model")
    entity_triggered = False
    entity_active = False
    entity_response = ""
    entity_timer = 0
    entity_alpha = 255

    # Loop principale
    running = True
    screen_w, screen_h = screen.get_size()

    while running:
        screen.blit(background_image, (0, 0))

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            if event.type == pygame.KEYDOWN and event.key == pygame.K_RETURN:
                # Se siamo all'ultima battuta → trigger finale + immagine conclusiva
                if dialog_manager.current_line == len(dialog_manager.dialog_lines) - 1 and not entity_triggered:
                    context = build_dialog_context(dialog_manager)
                    risposta_entita = entity.generate_response(f"{context}\nENTITÀ:") or "..."
                    CHANNEL_GLITCH.play(glitch_sound)

                    scrivi_blocco_note(risposta_entita)
                    dialog_manager.dialog_lines.append(("ENTITÀ", risposta_entita))

                    entity_active = True
                    entity_response = risposta_entita
                    entity_timer = pygame.time.get_ticks()
                    entity_alpha = 255

                    entity_triggered = True
                    # Finale visivo + audio (blocca ed esce)
                    mostra_finale(screen, screen_w, screen_h)
                    pygame.quit()
                    os._exit(0)
                else:
                    dialog_manager.next_line()

                    # Intervento casuale ENTITÀ durante battute di IO
                    if dialog_manager.current_line > 0:
                        prev = dialog_manager.dialog_lines[dialog_manager.current_line - 1]
                        if isinstance(prev, (list, tuple)):
                            spk = prev[0] if len(prev) >= 1 else None
                            txt = prev[1] if len(prev) >= 2 else ""
                        else:
                            spk, txt = None, ""

                        if spk == "IO" and not entity_active and random.random() < 0.30:
                            risposta = entity.generate_response(f"{txt}\nENTITÀ:")
                            if risposta:
                                CHANNEL_GLITCH.play(glitch_sound)
                                scrivi_blocco_note(risposta)
                                entity_active = True
                                entity_response = risposta
                                entity_timer = pygame.time.get_ticks()
                                entity_alpha = 255

        # UI dialoghi
        dialog_manager.draw(screen)

        # Overlay ENTITÀ con fade-out
        if entity_active:
            elapsed = pygame.time.get_ticks() - entity_timer
            full_text = "ENTITÀ: " + entity_response.strip().capitalize()
            text_surface = render_text_with_outline(full_text, ENTITY_FONT, (255, 55, 55))
            text_surface.set_alpha(entity_alpha)
            rect = text_surface.get_rect(center=(screen_w // 2, screen_h // 2 - 100))
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
