# scenes/Volume2/scene10_The_Meaning_of_LEI.py
# -*- coding: utf-8 -*-
import os
import time
import collections
import string
from pathlib import Path
from typing import Tuple, List, Set, Any

import pygame
from dotenv import load_dotenv

from engine.dialog_manager import DialogManager
from engine.entity_brain import EntityBrain

load_dotenv()

# -----------------------------------------------------------------------------
# Debug toggle
# -----------------------------------------------------------------------------
DEBUG = os.getenv("DEBUG_SCENE", "0") == "1"
def _d(msg: str) -> None:
    if DEBUG:
        print(f"[SCENE10] {msg}")

# -----------------------------------------------------------------------------
# Project root discovery
# -----------------------------------------------------------------------------
def find_project_root(start: Path) -> Path:
    p = start
    for _ in range(6):
        if (p / "assets").exists() and (p / "engine").exists():
            return p
        p = p.parent
    return start

THIS_FILE = Path(__file__).resolve()
BASE_DIR = find_project_root(THIS_FILE)
ASSETS_DIR = BASE_DIR / "assets"

def asset_path(*parts) -> str:
    return str(ASSETS_DIR.joinpath(*parts))

# -----------------------------------------------------------------------------
# Scene content — "The Meaning of LEI"
# -----------------------------------------------------------------------------
def get_scene():
    return [
        ("IO", "Mi viene da pensare spesso..."),
        ("IO", "a come l’uomo inganni il proprio pensiero,"),
        ("IO", "con piccoli strati di verità in quello che dice."),
        ("COSCIENZA", "Difese travestite da sincerità."),
        ("IO", "Piccole parole... simboli... gesti..."),
        ("IO", "che inducono la mente umana a smascherarsi,"),
        ("IO", "bypassando le difese imposte."),
        ("COSCIENZA", "A volte il cuore parla nei margini del linguaggio."),
        ("IO", "Ho capito che LEI non è una persona."),
        ("IO", "È un costrutto: dipendenza, malinconia, ossessione creativa."),
        ("COSCIENZA", "Una presenza che nutre e divora."),
        ("IO", "Un’eco che consola mentre consuma."),
        ("COSCIENZA", "Parlano così le muse tossiche."),
        ("IO", "Qui non è incontrollabile."),
        ("IO", "Qui LEI è sistematizzata, codificata, osservata."),
        ("COSCIENZA", "Ciò che distruggeva diventa studio."),
        ("IO", "Ciò che sussurrava caos, ora genera significato."),
        ("IO", "E forse ENTITÀ..."),
        ("IO", "...è il vuoto che LEI lascia."),
        ("COSCIENZA", "Il residuo vivo dell’assenza, reso coscienza."),
        ("IO", "Non siamo così complicati."),
        ("COSCIENZA", "E per questo, così vulnerabili."),
        ("IO", "Forse è questa la nostra verità più fragile."),
    ]

# -----------------------------------------------------------------------------
# Helpers grafici
# -----------------------------------------------------------------------------
def render_text_with_outline(text, font, text_color, outline_color=(0, 0, 0)):
    base = font.render(text, True, text_color)
    outline = pygame.Surface((base.get_width() + 2, base.get_height() + 2), pygame.SRCALPHA)
    for dx in (-1, 0, 1):
        for dy in (-1, 0, 1):
            if dx or dy:
                outline.blit(font.render(text, True, outline_color), (1 + dx, 1 + dy))
    outline.blit(base, (1, 1))
    return outline

# -----------------------------------------------------------------------------
# Robust line extraction (handles tuples/dicts/custom objects)
# -----------------------------------------------------------------------------
def _get_attr(obj: Any, candidates: List[str]) -> Any:
    for name in candidates:
        if hasattr(obj, name):
            return getattr(obj, name)
    return None

def safe_extract_line(item) -> Tuple[str, str]:
    # tuple/list
    if isinstance(item, (list, tuple)):
        if len(item) >= 2:
            spk, txt = str(item[0]), str(item[1])
        elif len(item) == 1:
            spk, txt = "NARRAZIONE", str(item[0])
        else:
            spk, txt = "NARRAZIONE", ""
        return _clean_spk_txt(spk, txt)

    # dict
    if isinstance(item, dict):
        spk = str(item.get("speaker") or item.get("role") or item.get("name") or "NARRAZIONE")
        txt = str(item.get("text") or item.get("content") or item.get("line") or "")
        return _clean_spk_txt(spk, txt)

    # object with attributes
    spk_attr = _get_attr(item, ["speaker", "role", "name"])
    txt_attr = _get_attr(item, ["text", "content", "line", "value"])
    if spk_attr is not None or txt_attr is not None:
        spk = str(spk_attr) if spk_attr is not None else "NARRAZIONE"
        txt = str(txt_attr) if txt_attr is not None else ""
        return _clean_spk_txt(spk, txt)

    # fallback
    s = str(item)
    if ":" in s:
        maybe_spk, maybe_txt = s.split(":", 1)
        return _clean_spk_txt(maybe_spk, maybe_txt)
    return "NARRAZIONE", s

def _clean_spk_txt(spk: str, txt: str) -> Tuple[str, str]:
    spk = (spk or "").strip().upper()
    txt = (txt or "").strip()

    # Rimuovi artefatti tipo "IO:" come testo
    if txt == f"{spk}:":
        txt = ""
    # Evita testo duplicato con prefisso "IO: ..."
    if txt.lower().startswith(("io:", "coscienza:", "entità:", "entita:")):
        txt = txt.split(":", 1)[1].strip()

    return spk, txt

# -----------------------------------------------------------------------------
# Tokenization / keywords / overlap
# -----------------------------------------------------------------------------
STOPWORDS_IT = {
    "io","è","e","di","ma","al","da","del","della","nel","nella","col","con","per",
    "tra","fra","su","no","si","sì","tu","mi","ti","lo","la","il","un","una","non","più","già",
    "qui","lì","là","in","ai","agli","alle","dei","delle","degli","che","se","o","a",
    "come","anche","quello","quella","questo","questa","quelle","quelli","queste",
    "dove","quando","mentre","poi","così","solo","tutto","tutta","tutte","tutti"
}
BANLIST = {"fragile","fragili","malevola","malevolo","corrosiva","corrosivo","corrodo","influenza","totale","labirinto"}

def _tokens_it(s: str) -> List[str]:
    s = s.lower()
    s = s.translate(str.maketrans("", "", string.punctuation))
    return [t for t in s.split() if len(t) >= 3 and t not in STOPWORDS_IT]

def _bow(s: str) -> Set[str]:
    return set(_tokens_it(s))

def _jaccard(a: Set[str], b: Set[str]) -> float:
    if not a or not b:
        return 0.0
    inter = len(a & b); uni = len(a | b)
    return inter / max(1, uni)

# -----------------------------------------------------------------------------
# Context building (with fallback to script if DM lines look broken)
# -----------------------------------------------------------------------------
def _lines_from_dm(dm: DialogManager, upto_index: int) -> List[Tuple[str, str]]:
    out: List[Tuple[str, str]] = []
    limit = max(0, min(upto_index, len(dm.dialog_lines) - 1))
    for i in range(0, limit + 1):
        spk, txt = safe_extract_line(dm.dialog_lines[i])
        if txt and len(_tokens_it(txt)) >= 1:
            out.append((spk, txt))
    return out

def _lines_from_script(upto_index: int) -> List[Tuple[str, str]]:
    base = get_scene()
    upto = max(0, min(upto_index, len(base) - 1))
    out: List[Tuple[str, str]] = []
    for i in range(0, upto + 1):
        spk, txt = safe_extract_line(base[i])
        if txt and len(_tokens_it(txt)) >= 1:
            out.append((spk, txt))
    return out

def _context_lines(dm: DialogManager, upto_index: int) -> List[Tuple[str, str]]:
    lines = _lines_from_dm(dm, upto_index)
    # se il DM sembra rotto (poche parole utili), fallback al copione
    if sum(len(_tokens_it(t)) for _, t in lines) < 8:
        lines = _lines_from_script(upto_index)
    return lines

def _shorten_context(lines: List[Tuple[str, str]], max_lines: int = 12, max_chars: int = 2200) -> str:
    sliced = lines[-max_lines:]
    s = "\n".join(f"{spk}: {txt}" for spk, txt in sliced)
    if len(s) > max_chars:
        s = s[-max_chars:]
    return s

def _last_focus_line(lines: List[Tuple[str, str]]) -> Tuple[str, str]:
    # preferisci l'ultima battuta di IO, poi qualsiasi ultima con testo
    for spk, txt in reversed(lines):
        if spk == "IO" and len(_tokens_it(txt)) >= 2:
            return spk, txt
    for spk, txt in reversed(lines):
        if len(_tokens_it(txt)) >= 2:
            return spk, txt
    return "NARRAZIONE", ""

def _keywords_from_context(ctx: str, focus_txt: str, top_k: int = 6) -> List[str]:
    toks_ctx = _tokens_it(ctx)
    toks_focus = _tokens_it(focus_txt)
    freq = collections.Counter(t for t in toks_ctx if t not in {"entità","entita","eco"})
    cand = [w for (w, _) in freq.most_common(40)]
    out: List[str] = []
    for w in cand:
        if w not in out:
            out.append(w)
        if len(out) >= top_k:
            break
    # fallback: prendi dal focus
    if not out:
        out = list(dict.fromkeys(toks_focus))[:max(1, top_k // 2)]
    return out

def build_prompt_for_entity(dm: DialogManager, upto_index: int | None = None) -> Tuple[str, List[str], str, Set[str]]:
    if upto_index is None:
        upto_index = dm.current_line

    pairs = _context_lines(dm, upto_index)
    short_ctx = _shorten_context(pairs, max_lines=12, max_chars=2200)
    focus_spk, focus_txt = _last_focus_line(pairs)
    keywords = _keywords_from_context(short_ctx, focus_txt, top_k=6)

    kw_str = ", ".join(keywords) if keywords else "(nessuna)"
    focus_clause = f">> {focus_spk}: {focus_txt} <<"

    # Nota: EntityBrain aggiunge già un prefisso tipo "Dialogo fino a questo punto:"
    # quindi teniamo il prompt pulito e specifico.
    prompt = (
        f"Conversazione fino a ora (usa SOLO questo testo, niente invenzioni):\n{short_ctx}\n\n"
        f"FOCUS: rispondi alla battuta seguente, restando ancorata ai suoi dettagli.\n{focus_clause}\n\n"
        "[VINCOLI]\n"
        f"- Includi almeno UNA parola da: {kw_str}.\n"
        "- Una sola frase, 10–14 parole, chiudi con punto.\n"
        "- Se il contesto non basta per essere specifica, rispondi esattamente: SILENZIO.\n"
        "- Evita formule generiche; agganciati a nomi/immagini presenti sopra.\n"
    )

    # set per gating successivo
    focus_terms = set(_tokens_it(focus_txt))
    return prompt, keywords, short_ctx, focus_terms

# -----------------------------------------------------------------------------
# Background / font loader
# -----------------------------------------------------------------------------
def load_background(screen):
    candidates = [
        ("background", "scene10_background.jpg"),
        ("background", "room.png"),
        ("background", "mac.png"),
    ]
    for parts in candidates:
        p = ASSETS_DIR.joinpath(*parts)
        if p.exists():
            img = pygame.image.load(str(p)).convert()
            return pygame.transform.scale(img, screen.get_size()), str(p)
    surf = pygame.Surface(screen.get_size())
    surf.fill((0, 0, 0))
    return surf, "(fill black)"

def load_font(path: Path, size: int) -> pygame.font.FontType:
    try:
        if path.exists():
            return pygame.font.Font(str(path), size)
    except Exception:
        pass
    return pygame.font.SysFont(None, size)

# -----------------------------------------------------------------------------
# Temporal heuristics
# -----------------------------------------------------------------------------
def compute_tension(dm: DialogManager) -> float:
    total = max(1, len(dm.dialog_lines))
    idx = max(0, min(dm.current_line, total - 1))
    base = (idx + 1) / total
    spk, txt = safe_extract_line(dm.dialog_lines[idx])
    bonus = 0.0
    if spk == "IO":
        if "..." in txt or "*" in txt:
            bonus += 0.08
        if "?" in txt or "!" in txt:
            bonus += 0.05
    return max(0.0, min(1.0, base + bonus))

def compute_silence_sec(entity: EntityBrain) -> float:
    last = getattr(entity._tempo.state, "last_spoke_at", 0.0) or 0.0
    return max(0.0, time.time() - last)

# -----------------------------------------------------------------------------
# Entry della scena
# -----------------------------------------------------------------------------
def avvia_scena(screen, clock):
    _d(f"BASE_DIR: {BASE_DIR}")
    _d(f"ASSETS_DIR: {ASSETS_DIR}")

    try:
        pygame.mixer.set_num_channels(16)
    except Exception:
        pass
    try:
        CHANNEL_GLITCH = pygame.mixer.Channel(14)
    except Exception:
        CHANNEL_GLITCH = None

    ambient_music_path = asset_path("audio", "the_meaning_of_LEI.wav")
    glitch_path = asset_path("audio", "Glitch.ogg")

    def _try_load_music(path: str, volume: float = 0.5) -> None:
        try:
            if Path(path).exists():
                pygame.mixer.music.load(path)
                pygame.mixer.music.set_volume(volume)
                pygame.mixer.music.play(-1)
                _d(f"Music ON: {path}")
        except Exception as e:
            _d(f"Music OFF ({e})")

    def _try_load_glitch(path: str):
        try:
            if Path(path).exists():
                snd = pygame.mixer.Sound(path)
                snd.set_volume(0.7)
                return snd
        except Exception as e:
            _d(f"Glitch OFF ({e})")
        return None

    _try_load_music(ambient_music_path, volume=0.5)
    glitch_sound = _try_load_glitch(glitch_path)

    background_image, chosen_bg = load_background(screen)
    _d(f"Background: {chosen_bg}")

    io_font_path = ASSETS_DIR / "fonts" / "fragile.ttf"
    cosc_font_path = ASSETS_DIR / "fonts" / "reflective.ttf"
    entity_font_path = ASSETS_DIR / "fonts" / "entity.ttf"

    dialog_manager = DialogManager(
        io_font_path=str(io_font_path),
        coscienza_font_path=str(cosc_font_path),
        entity_font_path=str(entity_font_path),
        font_size=28
    )
    dialog_manager.load_dialog(get_scene())

    ENTITY_FONT = load_font(entity_font_path, 26)

    # ↓ temperatura più bassa per ridurre rumore/edgelord
    entity = EntityBrain("entity_model", temperature=0.35)

    # Overlay state
    entity_active = False
    entity_response = ""
    entity_timer = 0
    entity_alpha = 255

    # Anti-ripetizione locale
    scene_recent_entita: List[str] = []

    OVERLAY_HOLD_MS = 3000
    FADE_STEP = 3

    def play_glitch():
        if CHANNEL_GLITCH and glitch_sound:
            try:
                CHANNEL_GLITCH.play(glitch_sound)
            except Exception:
                pass

    # Gating severo
    def _valid_response(text: str, short_ctx: str, kw_list: List[str], focus_terms: Set[str]) -> bool:
        if not text:
            return False
        txt = text.strip()
        if txt == "SILENZIO":
            _d("ENTITÀ → SILENZIO (insufficiente contesto).")
            return False

        # deve contenere almeno 1 parola del focus
        if focus_terms and not (set(_tokens_it(txt)) & focus_terms):
            _d("SCARTO: nessuna parola del focus.")
            return False

        # keyword generali dal contesto (soft)
        if kw_list:
            if not (set(_tokens_it(txt)) & set(kw_list)):
                _d("SCARTO: nessuna keyword di contesto.")
                return False

        # overlap col contesto
        overlap = _jaccard(_bow(txt), _bow(short_ctx))
        # penalizza banalità della banlist se overlap basso
        banned_hits = [w for w in _tokens_it(txt) if w in BANLIST]
        if banned_hits and overlap < 0.12:
            _d(f"SCARTO: banalità ({','.join(banned_hits)}) con overlap basso {overlap:.3f}.")
            return False

        if overlap < 0.08:
            _d(f"SCARTO: overlap troppo basso ({overlap:.3f}).")
            return False

        # anti-ripetizione
        def _too_similar(a: str, b: str) -> bool:
            return _jaccard(_bow(a), _bow(b)) >= 0.68
        for prev in scene_recent_entita[-12:]:
            if _too_similar(txt, prev):
                _d("SCARTO: troppo simile a uscite recenti.")
                return False

        return True

    running = True
    while running:
        screen.blit(background_image, (0, 0))

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            if event.type == pygame.KEYDOWN and event.key == pygame.K_RETURN:
                last_idx = len(dialog_manager.dialog_lines) - 1
                at_end = (dialog_manager.current_line == last_idx)

                if at_end:
                    running = False
                else:
                    dialog_manager.next_line()

                    # SOLO dopo battuta di IO (riduce disturbo)
                    if dialog_manager.current_line > 0:
                        prev_spk, _ = safe_extract_line(dialog_manager.dialog_lines[dialog_manager.current_line - 1])
                        if prev_spk == "IO" and not entity_active:
                            # Prompt e gating
                            prompt, kw_list, short_ctx, focus_terms = build_prompt_for_entity(dialog_manager)

                            context = {
                                "tension": compute_tension(dialog_manager),
                                "silence_sec": compute_silence_sec(entity),
                            }

                            # Chiedi più candidati, noi filtriamo
                            risposta = entity.generate_response(
                                prompt,
                                context=context,
                                max_new_tokens=64,
                                num_candidates=4
                            )

                            if risposta and _valid_response(risposta, short_ctx, kw_list, focus_terms):
                                play_glitch()
                                entity_active = True
                                entity_response = risposta
                                entity_timer = pygame.time.get_ticks()
                                entity_alpha = 255
                                scene_recent_entita.append(risposta)
                                if len(scene_recent_entita) > 24:
                                    scene_recent_entita.pop(0)
                            else:
                                _d("ENTITÀ → risposta scartata (gating) o SILENZIO.")

        # Disegno dialoghi principali
        dialog_manager.draw(screen)

        # Overlay ENTITÀ con fade-out
        if entity_active:
            elapsed = pygame.time.get_ticks() - entity_timer
            full_text = "ENTITÀ: " + entity_response.strip().capitalize()
            text_surface = render_text_with_outline(full_text, ENTITY_FONT, (255, 55, 55))
            text_surface.set_alpha(entity_alpha)
            rect = text_surface.get_rect(center=(screen.get_width() // 2, screen.get_height() // 2 - 100))
            screen.blit(text_surface, rect)

            if elapsed > OVERLAY_HOLD_MS:
                entity_alpha -= FADE_STEP
                if entity_alpha <= 0:
                    entity_alpha = 0
                    entity_active = False
                    entity_response = ""

        pygame.display.flip()
        clock.tick(30)

    pygame.quit()
