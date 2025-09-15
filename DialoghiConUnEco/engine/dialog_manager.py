import pygame
import textwrap

class DialogManager:
    def __init__(self, io_font_path=None, coscienza_font_path=None, entity_font_path=None,
                 font_size=28, screen_width=1280, screen_height=1024):
        # Carica i font per i tre speaker (IO, COSCIENZA, ENTITÀ).
        # Se non viene fornito un percorso al font, usa di default "consolas".
        self.fonts = {
            "IO": pygame.font.Font(io_font_path, font_size) if io_font_path else pygame.font.SysFont("consolas", font_size),
            "COSCIENZA": pygame.font.Font(coscienza_font_path, font_size) if coscienza_font_path else pygame.font.SysFont("consolas", font_size),
            "ENTITÀ": pygame.font.Font(entity_font_path, font_size) if entity_font_path else pygame.font.SysFont("consolas", font_size),
        }

        self.font_size = font_size
        self.screen_width = screen_width
        self.screen_height = screen_height

        # Calcola la larghezza media di un carattere per il font di IO.
        avg_char_width = self.fonts["IO"].size("A")[0]

        # Calcola quante lettere possono stare in una riga (wrap).
        # Usa la larghezza dello schermo divisa per la larghezza media di un carattere.
        # Sottrae 10 per avere margine di sicurezza.
        self.wrap_width = screen_width // avg_char_width - 10

        # Qui verranno salvate le righe di dialogo già "wrappate".
        self.dialog_lines = []

        # Indice della riga attualmente visualizzata.
        self.current_line = 0

    def load_dialog(self, dialog_list):
        """Carica un nuovo dialogo e lo spezza in righe in base alla wrap_width"""
        self.dialog_lines = []

        for item in dialog_list:
            # Caso standard: tupla (speaker, testo)
            if len(item) == 2:
                speaker, text = item
                prefix = f"{speaker}:"
            # Caso alternativo: tupla (speaker, prefisso personalizzato, testo)
            elif len(item) == 3:
                speaker, prefix, text = item
            else:
                raise ValueError("Ogni riga del dialogo deve avere 2 o 3 elementi.")

            # Spezza il testo in righe multiple in base alla wrap_width
            wrapped_text = textwrap.wrap(text, self.wrap_width)

            # Per la prima riga aggiunge anche il prefisso (es. "IO:")
            for i, line in enumerate(wrapped_text):
                line_prefix = prefix if i == 0 else ""
                self.dialog_lines.append((speaker, line_prefix, line))

        # Resetta il dialogo alla prima riga
        self.current_line = 0

    def next_line(self):
        """Passa alla riga successiva del dialogo"""
        if self.current_line < len(self.dialog_lines) - 1:
            self.current_line += 1

    def draw(self, screen):
        """Disegna sullo schermo la riga corrente del dialogo"""
        if self.current_line >= len(self.dialog_lines):
            return

        # Prende la riga corrente
        speaker, prefix, text = self._unpack_line(self.dialog_lines[self.current_line])

        # Sceglie il font giusto in base allo speaker
        font = self.fonts.get(speaker, pygame.font.SysFont("consolas", self.font_size))

        # Colore testo: COSCIENZA è verde, gli altri bianchi
        text_color = (0, 255, 0) if speaker == "COSCIENZA" else (255, 255, 255)

        # Coordinate di base (in basso allo schermo)
        start_x = 80
        start_y = int(self.screen_height * 0.80)

        # Disegna il prefisso (es. "IO:")
        if prefix:
            prefix_surface = self._render_text_with_outline(prefix, font, text_color)
            screen.blit(prefix_surface, (start_x, start_y))

        # Disegna il testo subito sotto il prefisso
        text_surface = self._render_text_with_outline(text, font, text_color)
        screen.blit(text_surface, (start_x, start_y + self.font_size + 5))

    def _unpack_line(self, line):
        """Gestisce tuple da 2 o 3 elementi e restituisce sempre (speaker, prefix, text)"""
        if len(line) == 3:
            return line
        elif len(line) == 2:
            speaker, text = line
            return speaker, f"{speaker}:", text
        else:
            raise ValueError("Linea dialogo malformata.")

    def _render_text_with_outline(self, text, font, text_color, outline_color=(0, 0, 0)):
        """Renderizza testo con bordo nero per migliorarne la leggibilità"""
        base = font.render(text, True, text_color)

        # Crea una superficie leggermente più grande del testo
        outline = pygame.Surface((base.get_width() + 2, base.get_height() + 2), pygame.SRCALPHA)

        # Disegna il contorno attorno al testo (8 direzioni)
        for dx in [-1, 0, 1]:
            for dy in [-1, 0, 1]:
                if dx != 0 or dy != 0:
                    outline.blit(font.render(text, True, outline_color), (1 + dx, 1 + dy))

        # Sovrappone il testo principale al centro
        outline.blit(base, (1, 1))
        return outline
