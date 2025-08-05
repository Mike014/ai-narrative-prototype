import pygame
import sys
import random

def mostra_menu(screen, clock):
    # Setup audio del menu
    pygame.mixer.music.load("assets/audio/menu_theme.wav")
    pygame.mixer.music.set_volume(0.185)
    pygame.mixer.music.play(-1)

    glitch_scroll_sound = pygame.mixer.Sound("assets/audio/glitch_scroll.ogg")
    glitch_scroll_sound.set_volume(0.75)

    FONT = pygame.font.Font("assets/fonts/reflective.ttf", 48)

    menu_items = ["Inizia", "Crediti", "Esci"]
    selected_index = 0
    alpha_values = [150 for _ in menu_items]

    running = True
    while running:
        screen.fill((10, 10, 10))

        for i, item in enumerate(menu_items):
            color = (255, 55, 55) if i == selected_index else (180, 180, 180)
            alpha_values[i] = min(255, alpha_values[i] + 15) if i == selected_index else max(150, alpha_values[i] - 15)

            jitter_x = random.randint(-2, 2) if i == selected_index else 0
            jitter_y = random.randint(-2, 2) if i == selected_index else 0

            text_surface = FONT.render(item, True, color)
            text_surface.set_alpha(alpha_values[i])
            rect = text_surface.get_rect(center=(640 + jitter_x, 300 + i * 80 + jitter_y))
            screen.blit(text_surface, rect)

        pygame.display.flip()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_UP:
                    selected_index = (selected_index - 1) % len(menu_items)
                    glitch_scroll_sound.play()
                elif event.key == pygame.K_DOWN:
                    selected_index = (selected_index + 1) % len(menu_items)
                    glitch_scroll_sound.play()
                elif event.key == pygame.K_RETURN:
                    pygame.mixer.music.fadeout(1000)
                    if menu_items[selected_index] == "Inizia":
                        return "inizia"
                    elif menu_items[selected_index] == "Crediti":
                        print("Creato da Michele Grimaldi")
                    elif menu_items[selected_index] == "Esci":
                        return "esci"

        clock.tick(30)
