import pygame
import sys
from scenes import scene1
from menu import mostra_menu


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
        scene1.avvia_scena(screen, clock)
    elif scelta == "crediti":
        # Qui puoi importare e chiamare scene_crediti.avvia_crediti()
        print("TODO: scena crediti")
    elif scelta == "esci":
        pygame.quit()
        sys.exit()


if __name__ == "__main__":
    main()
