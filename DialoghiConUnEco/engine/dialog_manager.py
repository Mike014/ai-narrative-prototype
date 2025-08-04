# Gestione dei dialoghi
import pygame
import textwrap

class DialogManager:
    def __init__(self, io_font_path=None, coscienza_font_path=None, entity_font_path=None, font_size=24, wrap_width=60):
        self.fonts = {
            "IO": pygame.font.Font(io_font_path, font_size) if io_font_path else pygame.font.SysFont("consolas", font_size),
            "COSCIENZA": pygame.font.Font(coscienza_font_path, font_size) if coscienza_font_path else pygame.font.SysFont("consolas", font_size),
            "ENTITÀ": pygame.font.Font(entity_font_path, font_size) if entity_font_path else pygame.font.SysFont("consolas", font_size),
        }
        self.wrap_width = wrap_width
        self.dialog_lines = []
        self.current_line = 0

    def load_dialog(self, dialog_list):
        self.dialog_lines = []
        for speaker, text in dialog_list:
            wrapped_text = textwrap.wrap(text, self.wrap_width)
            for i, line in enumerate(wrapped_text):
                prefix = f"{speaker}:" if i == 0 else ""
                self.dialog_lines.append((speaker, prefix, line))
        self.current_line = 0

    def next_line(self):
        if self.current_line < len(self.dialog_lines) - 1:
            self.current_line += 1

    def draw(self, screen):
        if self.current_line >= len(self.dialog_lines):
            return

        speaker, prefix, text = self.dialog_lines[self.current_line]
        font = self.fonts.get(speaker, pygame.font.SysFont("consolas", 24))

        def render_text_with_outline(text, font, text_color, outline_color=(0, 0, 0)):
            base = font.render(text, True, text_color)
            outline = pygame.Surface((base.get_width() + 2, base.get_height() + 2), pygame.SRCALPHA)
            for dx in [-1, 0, 1]:
                for dy in [-1, 0, 1]:
                    if dx != 0 or dy != 0:
                        pos = (1 + dx, 1 + dy)
                        outline.blit(font.render(text, True, outline_color), pos)
            outline.blit(base, (1, 1))
            return outline

        # Colori personalizzati per personaggi
        if speaker == "COSCIENZA":
            text_color = (0, 255, 0)  # verde tipo terminale
        else:
            text_color = (255, 255, 255)

        speaker_surface = render_text_with_outline(prefix, font, text_color)
        text_surface = render_text_with_outline(text, font, text_color)

        screen.blit(speaker_surface, (50, 450))
        screen.blit(text_surface, (50, 480))
