import pygame
import sys
from menu import mostra_menu

# Import scene modules (Volume 1)
from scenes.Volume1 import scene1_diary_breaks
from scenes.Volume1 import scene2_echo_speaks
from scenes.Volume1 import scene3_voice_entita
from scenes.Volume1 import scene4_os_collapse
from scenes.Volume1 import scene5_what_am_i

# -----------------------------------------------------------------------------
# Setup audio + pygame
# -----------------------------------------------------------------------------
pygame.mixer.pre_init(frequency=44100, size=-16, channels=2, buffer=2048)
pygame.init()
pygame.mixer.set_num_channels(16)
pygame.mixer.set_reserved(2)

# -----------------------------------------------------------------------------
# Scene map per Volume 1: titolo → (modulo, funzione da chiamare)
# -----------------------------------------------------------------------------
VOLUME1_SCENES = {
    "The Diary Breaks": (scene1_diary_breaks, "avvia_scena"),
    "When the Echo Speaks": (scene2_echo_speaks, "avvia_scena"),
    "The Voice of ENTITA’": (scene3_voice_entita, "avvia_scena"),
    "The OS Collapse": (scene4_os_collapse, "avvia_scena"),
    "What Am I?": (scene5_what_am_i, "run_intro"),
}

# -----------------------------------------------------------------------------
# UI helper: lista verticale con titolo
# -----------------------------------------------------------------------------
def draw_list_menu(screen, clock, title, options, initial_index=0):
    """
    Ritorna la stringa selezionata oppure None se l'utente torna indietro (ESC/Backspace).
    """
    try:
        title_font = pygame.font.SysFont("consolas", 56)
        item_font  = pygame.font.SysFont("consolas", 44)
        hint_font  = pygame.font.SysFont("consolas", 22)
    except Exception:
        title_font = pygame.font.Font(None, 56)
        item_font  = pygame.font.Font(None, 44)
        hint_font  = pygame.font.Font(None, 22)

    selected = initial_index

    while True:
        screen.fill((0, 0, 0))

        # Titolo
        title_surf = title_font.render(title, True, (200, 200, 255))
        title_rect = title_surf.get_rect(center=(screen.get_width() // 2, 160))
        screen.blit(title_surf, title_rect)

        # Opzioni
        start_y = 280
        line_h = 70
        for i, opt in enumerate(options):
            color = (255, 70, 70) if i == selected else (235, 235, 235)
            surf = item_font.render(opt, True, color)
            rect = surf.get_rect(center=(screen.get_width() // 2, start_y + i * line_h))
            screen.blit(surf, rect)

        # Hints
        hint = hint_font.render("↑↓ per muoverti  •  INVIO per selezionare  •  ESC per tornare indietro", True, (140, 140, 140))
        screen.blit(hint, (screen.get_width()//2 - hint.get_width()//2, screen.get_height() - 60))

        pygame.display.flip()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit(0)
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE or event.key == pygame.K_BACKSPACE:
                    return None
                elif event.key == pygame.K_UP:
                    selected = (selected - 1) % len(options)
                elif event.key == pygame.K_DOWN:
                    selected = (selected + 1) % len(options)
                elif event.key == pygame.K_RETURN:
                    return options[selected]

        clock.tick(60)

# -----------------------------------------------------------------------------
# Menu Volume
# -----------------------------------------------------------------------------
def mostra_volumi(screen, clock):
    options = ["Volume 1", "Torna indietro"]
    sel = draw_list_menu(screen, clock, "SELEZIONA VOLUME", options)
    if sel == "Volume 1":
        return "volume1"
    return None

def mostra_scelta_scene_volume1(screen, clock):
    options = list(VOLUME1_SCENES.keys()) + ["Torna indietro"]
    sel = draw_list_menu(screen, clock, "VOLUME 1", options)
    if sel == "Torna indietro" or sel is None:
        return None
    return sel

# -----------------------------------------------------------------------------
# Main loop
# -----------------------------------------------------------------------------
def main():
    print("Avvio gioco...")
    pygame.init()
    pygame.mixer.init()

    screen = pygame.display.set_mode((1280, 960))
    pygame.display.set_caption("Dialoghi con un’Eco")
    clock = pygame.time.Clock()

    while True:
        scelta = mostra_menu(screen, clock)  # il tuo menu principale esistente

        if scelta == "inizia":
            volume = mostra_volumi(screen, clock)
            if volume == "volume1":
                scena = mostra_scelta_scene_volume1(screen, clock)
                if scena and scena in VOLUME1_SCENES:
                    module, func_name = VOLUME1_SCENES[scena]
                    # Avvio scena
                    getattr(module, func_name)(screen, clock)
                    # Al ritorno dalla scena si rientra al menu principale
                    continue
                # Torna al menu principale se annullato
                continue

        elif scelta == "crediti":
            # TODO: chiama la tua scena crediti quando pronta
            print("TODO: scena crediti")
            # piccolo delay per non rimbalzare subito
            pygame.time.delay(500)

        elif scelta == "esci":
            pygame.quit()
            sys.exit(0)

        else:
            # Protezione: se mostra_menu restituisce altro/None, ripresenta
            pygame.time.delay(100)

# -----------------------------------------------------------------------------
if __name__ == "__main__":
    main()
