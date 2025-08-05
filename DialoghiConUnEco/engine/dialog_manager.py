# engine/dialog_manager.py

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
        """Carica un nuovo dialogo e lo impacchetta con word wrap"""
        self.dialog_lines = []
        for item in dialog_list:
            if len(item) == 2:
                speaker, text = item
                prefix = f"{speaker}:"
            elif len(item) == 3:
                speaker, prefix, text = item
            else:
                raise ValueError("Ogni riga del dialogo deve essere una tupla con 2 o 3 elementi.")

            wrapped_text = textwrap.wrap(text, self.wrap_width)
            for i, line in enumerate(wrapped_text):
                line_prefix = prefix if i == 0 else ""
                self.dialog_lines.append((speaker, line_prefix, line))

        self.current_line = 0

    def next_line(self):
        """Passa alla riga successiva del dialogo"""
        if self.current_line < len(self.dialog_lines) - 1:
            self.current_line += 1

    def draw(self, screen):
        """Disegna la riga corrente del dialogo sullo schermo"""
        if self.current_line >= len(self.dialog_lines):
            return

        speaker, prefix, text = self._unpack_line(self.dialog_lines[self.current_line])
        font = self.fonts.get(speaker, pygame.font.SysFont("consolas", 24))

        text_color = (0, 255, 0) if speaker == "COSCIENZA" else (255, 255, 255)

        speaker_surface = self._render_text_with_outline(prefix, font, text_color)
        text_surface = self._render_text_with_outline(text, font, text_color)

        screen.blit(speaker_surface, (50, 450))
        screen.blit(text_surface, (50, 480))

    def _unpack_line(self, line):
        """Gestione compatibile per tuple da 2 o 3 elementi"""
        if len(line) == 3:
            return line
        elif len(line) == 2:
            speaker, text = line
            return speaker, f"{speaker}:", text
        else:
            raise ValueError("Linea dialogo malformata.")

    def _render_text_with_outline(self, text, font, text_color, outline_color=(0, 0, 0)):
        """Renderizza testo con bordo nero"""
        base = font.render(text, True, text_color)
        outline = pygame.Surface((base.get_width() + 2, base.get_height() + 2), pygame.SRCALPHA)
        for dx in [-1, 0, 1]:
            for dy in [-1, 0, 1]:
                if dx != 0 or dy != 0:
                    outline.blit(font.render(text, True, outline_color), (1 + dx, 1 + dy))
        outline.blit(base, (1, 1))
        return outline
