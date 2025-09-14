# menu.py
import pygame
import sys
import random
import time
import math
from typing import List, Tuple
import webbrowser


# ----------------------------- Utilità ----------------------------------------

def _safe_font(path: str, size: int):
    try:
        return pygame.font.Font(path, size)
    except Exception:
        return pygame.font.SysFont("arial", size)

def _load_bg_scaled(path: str, size: Tuple[int, int]) -> pygame.Surface:
    try:
        img = pygame.image.load(path).convert()
        return pygame.transform.smoothscale(img, size)
    except Exception:
        # fallback: schermo nero
        s = pygame.Surface(size)
        s.fill((10, 10, 10))
        return s.convert()

def _make_scanlines(size: Tuple[int, int], step: int = 2, alpha: int = 22) -> pygame.Surface:
    w, h = size
    scan = pygame.Surface((w, h), pygame.SRCALPHA)
    col = (0, 0, 0, alpha)
    y = 0
    while y < h:
        pygame.draw.line(scan, col, (0, y), (w, y))
        y += step
    return scan

def _make_vignette(size: Tuple[int, int], edge_alpha: int = 80) -> pygame.Surface:
    # vignette leggera ai bordi (economica: rettangoli trasparenti)
    w, h = size
    v = pygame.Surface((w, h), pygame.SRCALPHA)
    shade = (0, 0, 0, edge_alpha)
    border = max(40, w // 20)
    # top/bottom
    pygame.draw.rect(v, shade, (0, 0, w, border))
    pygame.draw.rect(v, shade, (0, h - border, w, border))
    # left/right
    pygame.draw.rect(v, shade, (0, 0, border, h))
    pygame.draw.rect(v, shade, (w - border, 0, border, h))
    return v

def _build_glitch_slices(height: int, n_slices: int = 10) -> List[Tuple[int, int, int]]:
    """Genera strisce orizzontali (y, h, dx) da spostare per effetto tearing."""
    out = []
    used = 0
    for _ in range(n_slices):
        h = random.randint(4, 30)
        y = random.randint(0, max(0, height - h))
        dx = random.randint(-18, 18)
        out.append((y, h, dx))
        used += h
    return out

# ----------------------------- Menu -------------------------------------------

def mostra_menu(screen: pygame.Surface, clock: pygame.time.Clock):
    # Audio background
    try:
        pygame.mixer.music.load("assets/audio/intro.wav")
        pygame.mixer.music.set_volume(1)
        pygame.mixer.music.play(0)
    except Exception:
        pass

    glitch_scroll_sound = None
    try:
        glitch_scroll_sound = pygame.mixer.Sound("assets/audio/glitch_scroll.ogg")
        glitch_scroll_sound.set_volume(0.55)
    except Exception:
        glitch_scroll_sound = None

    # Font
    FONT = _safe_font("assets/fonts/reflective.ttf", 48)
    FONT_SMALL = _safe_font("assets/fonts/Roboto_Mono/static/RobotoMono-Regular.ttf", 16)

    # Sfondo
    W, H = screen.get_size()
    bg_base = _load_bg_scaled("assets/background/menu.png", (W, H))
    overlay = pygame.Surface((W, H)).convert()
    overlay.set_colorkey(None)

    # Overlay cosmetici
    scanlines = _make_scanlines((W, H), step=2, alpha=18)
    vignette = _make_vignette((W, H), edge_alpha=70)

    # Stato menu
    menu_items = ["Inizia", "Crediti", "Esci"]
    selected_index = 0
    alpha_values = [150 for _ in menu_items]

    # Stato glitch
    glitch_active = False
    glitch_end_time = 0.0
    glitch_slices: List[Tuple[int, int, int]] = []
    flicker_phase = 0.0
    next_random_glitch = time.time() + random.uniform(1.2, 2.4)

    running = True
    t0 = time.time()

    while running:
        dt = clock.tick(60) / 1000.0
        t = time.time() - t0

        # Input
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_UP:
                    selected_index = (selected_index - 1) % len(menu_items)
                    if glitch_scroll_sound: glitch_scroll_sound.play()
                    # trigger glitch burst breve
                    glitch_active = True
                    glitch_end_time = time.time() + 0.14
                    glitch_slices = _build_glitch_slices(H, n_slices=random.randint(6, 12))

                elif event.key == pygame.K_DOWN:
                    selected_index = (selected_index + 1) % len(menu_items)
                    if glitch_scroll_sound: glitch_scroll_sound.play()
                    glitch_active = True
                    glitch_end_time = time.time() + 0.14
                    glitch_slices = _build_glitch_slices(H, n_slices=random.randint(6, 12))

                elif event.key == pygame.K_RETURN:
                    try:
                        pygame.mixer.music.fadeout(1000)
                    except Exception:
                        pass
                    choice = menu_items[selected_index]
                    if choice == "Inizia":
                        try: pygame.mixer.music.fadeout(1000)
                        except Exception: pass
                        return "inizia"
                    elif choice == "Crediti":
                        webbrowser.open("https://mike014.github.io/michele-portfolio/index.html", new=2)
                        print("Creato da Michele Grimaldi")
                    elif choice == "Esci":
                        try: pygame.mixer.music.fadeout(500)
                        except Exception: pass
                        return "esci"

        # Random glitch sporadico
        if time.time() > next_random_glitch and not glitch_active:
            glitch_active = True
            glitch_end_time = time.time() + random.uniform(0.10, 0.22)
            glitch_slices = _build_glitch_slices(H, n_slices=random.randint(4, 10))
            next_random_glitch = time.time() + random.uniform(1.5, 3.0)

        # Decadimento glitch
        if glitch_active and time.time() >= glitch_end_time:
            glitch_active = False

        # --- RENDER BACKGROUND (glitchabile) ---
        # Jitter sub-pixel simulato: 0–1 px orizzontale/verticale
        jitter_x = random.choice([-1, 0, 1])
        jitter_y = random.choice([-1, 0, 1])

        if not glitch_active:
            # draw liscio con leggero jitter
            screen.blit(bg_base, (jitter_x, jitter_y))
        else:
            # base
            screen.blit(bg_base, (0, 0))
            # tearing a strisce orizzontali
            for (y, h, dx) in glitch_slices:
                # ritaglia striscia dal bg e riblitta shiftata
                rect = pygame.Rect(0, y, W, h)
                slice_surf = bg_base.subsurface(rect)
                screen.blit(slice_surf, (dx, y))
            # flash leggero
            flash = pygame.Surface((W, H), pygame.SRCALPHA)
            flash.fill((255, 255, 255, 12))
            screen.blit(flash, (0, 0))

        # Scanlines + vignette
        screen.blit(scanlines, (0, 0))
        screen.blit(vignette, (0, 0))

        # Flicker globale molto lieve (respira)
        flicker_phase += dt * 2.6
        if math.sin(flicker_phase) > 0.8:
            f = pygame.Surface((W, H), pygame.SRCALPHA)
            f.fill((0, 0, 0, 18))
            screen.blit(f, (0, 0))

        # --- RENDER MENU ITEMS (glitch testo sul selezionato) ---
        cx = W // 2
        base_y = int(H * 0.42)
        step_y = 72

        for i, item in enumerate(menu_items):
            is_sel = (i == selected_index)

            # easing alpha
            if is_sel:
                alpha_values[i] = min(255, alpha_values[i] + 20)
            else:
                alpha_values[i] = max(140, alpha_values[i] - 20)

            # jitter selezione
            tx = cx + (random.randint(-2, 2) if is_sel else 0)
            ty = base_y + i * step_y + (random.randint(-2, 2) if is_sel else 0)

            if is_sel:
                # RGB split: ciano & rosso leggermente sfalsati + bianco centrale
                txt_cy = FONT.render(item, True, (80, 255, 255))
                txt_rd = FONT.render(item, True, (255, 60, 60))
                txt_wh = FONT.render(item, True, (230, 230, 230))
                for s in (txt_cy, txt_rd, txt_wh):
                    s.set_alpha(alpha_values[i])

                rect_base = txt_wh.get_rect(center=(tx, ty))
                rect_cy = txt_cy.get_rect(center=(tx - 2, ty))
                rect_rd = txt_rd.get_rect(center=(tx + 2, ty))

                screen.blit(txt_cy, rect_cy)
                screen.blit(txt_rd, rect_rd)
                screen.blit(txt_wh, rect_base)

                # micro righe glitch sulla riga selezionata
                if glitch_active:
                    for _ in range(2):
                        gy = rect_base.top + random.randint(0, rect_base.height - 2)
                        pygame.draw.line(screen, (255, 255, 255),
                                         (rect_base.left, gy), (rect_base.right, gy), 1)
            else:
                color = (180, 180, 180)
                txt = FONT.render(item, True, color)
                txt.set_alpha(alpha_values[i])
                rect = txt.get_rect(center=(tx, ty))
                screen.blit(txt, rect)

        # --- Footer discreto (opzionale) ---
        info = "Frecce scegli   Invio conferma"
        small = FONT_SMALL.render(info, True, (200, 200, 200))
        screen.blit(small, (W // 2 - small.get_width() // 2, int(H * 0.90)))

        pygame.display.flip()
