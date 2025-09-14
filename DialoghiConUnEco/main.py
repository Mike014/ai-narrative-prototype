import pygame
import sys
from scenes import scene1
from menu import mostra_menu

# Imposta il mixer in modo stabile per Windows + laptop moderni
pygame.mixer.pre_init(frequency=44100, size=-16, channels=2, buffer=2048)
pygame.init()

# Più canali e 2 riservati per effetti UI/ducking
pygame.mixer.set_num_channels(16)
pygame.mixer.set_reserved(2)


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
