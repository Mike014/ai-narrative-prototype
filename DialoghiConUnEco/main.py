import pygame
import sys
from scenes import scene1
from scenes import scene2
from scenes import scene3
from scenes import scene4
from menu import mostra_menu

# Imposta il mixer in modo stabile per Windows + laptop moderni
pygame.mixer.pre_init(frequency=44100, size=-16, channels=2, buffer=2048)
pygame.init()

# Più canali e 2 riservati per effetti UI/ducking
pygame.mixer.set_num_channels(16)
pygame.mixer.set_reserved(2)


def mostra_scelta_scene(screen, clock):
    """Mini-menu per scegliere quale scena avviare"""
    font = pygame.font.SysFont("consolas", 48)
    options = ["Scena 1", "Scena 2", "Scena 3", "Scena 4", "Torna indietro"]
    selected = 0

    choosing = True
    while choosing:
        screen.fill((0, 0, 0))

        for i, opt in enumerate(options):
            color = (255, 0, 0) if i == selected else (255, 255, 255)
            text_surface = font.render(opt, True, color)
            rect = text_surface.get_rect(center=(screen.get_width() // 2, 300 + i * 80))
            screen.blit(text_surface, rect)

        pygame.display.flip()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_UP:
                    selected = (selected - 1) % len(options)
                elif event.key == pygame.K_DOWN:
                    selected = (selected + 1) % len(options)
                elif event.key == pygame.K_RETURN:
                    if options[selected] == "Scena 1":
                        return "scene1"
                    elif options[selected] == "Scena 2":
                        return "scene2"
                    elif options[selected] == "Scena 3":
                        return "scene3"
                    elif options[selected] == "Scena 4":
                        return "scene4"
                    else:
                        return "indietro"

        clock.tick(30)


def main():
    print("Avvio gioco...")
    pygame.init()
    pygame.mixer.init()

    screen = pygame.display.set_mode((1280, 720))
    pygame.display.set_caption("Dialoghi con un’Eco")
    clock = pygame.time.Clock()

    # Avvia menu e aspetta selezione
    scelta = mostra_menu(screen, clock)

    if scelta == "inizia":
        scena_scelta = mostra_scelta_scene(screen, clock)
        if scena_scelta == "scene1":
            scene1.avvia_scena(screen, clock)
        elif scena_scelta == "scene2":
            scene2.avvia_scena(screen, clock)
        elif scena_scelta == "scene3":
            scene3.avvia_scena(screen, clock)
        elif scena_scelta == "scene4":
            scene4.avvia_scena(screen, clock)
        else:
            main()  # torna al menu principale

    elif scelta == "crediti":
        # Qui puoi importare e chiamare scene_crediti.avvia_crediti()
        print("TODO: scena crediti")

    elif scelta == "esci":
        pygame.quit()
        sys.exit()


if __name__ == "__main__":
    main()
