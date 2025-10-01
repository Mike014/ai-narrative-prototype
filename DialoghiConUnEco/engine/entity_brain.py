# engine/entity_brain.py
# -*- coding: utf-8 -*-

"""
ENTITÀ — Joker-mode (Ledger-inspired) per *Dialoghi con un’Eco*
Versione: 2025-10-01

Modifiche principali:
- Risponde sempre ai turni dell'utente (bypass del gate temporale su user_turn=True).
- Limiti di parole più elastici (9–16) + micro post-edit per rientrare nei limiti.
- Prompt più naturale: rimosse “parole chiave da includere”, coerenza domanda→risposta.
- Intenzione iniziale preferisce punchline; esperimenti/origini entrano dopo.
- Preclean e punteggiatura rafforzati (“punto”→“.”, chiusura con punto assicurata).
- Logging pulito (meno rumore httpx/httpcore).
"""

from __future__ import annotations

import os
import re
import csv
import math
import time
import random
import pathlib
import logging
from time import perf_counter
from dataclasses import dataclass
from typing import Optional, List, Tuple, Dict, Any
from enum import Enum
from pathlib import Path

from dotenv import load_dotenv
from groq import Groq


# ---------------------------------------------------------------------
# PyInstaller frozen path fix (PRIMA DI TUTTO)
# ---------------------------------------------------------------------
if getattr(__import__("sys"), "frozen", False):
    # Porta la working dir accanto all'eseguibile
    import sys as _sys
    os.chdir(Path(_sys.executable).parent)


def _load_env():
    """Se è un eseguibile PyInstaller, leggi .env.game accanto all’EXE,
    altrimenti usa il .env nella root del progetto se presente."""
    import sys as _sys
    base = Path(_sys.executable).parent if getattr(_sys, "frozen", False) else Path(__file__).resolve().parent
    for cand in (base / ".env.game", base.parent / ".env.game", base / ".env", base.parent / ".env"):
        if cand.exists():
            load_dotenv(cand)
            break


_load_env()

# ---------------------------------------------------------------------
# Logging pulito
# ---------------------------------------------------------------------
LOG_LEVEL = os.getenv("ENTITA_LOG_LEVEL", "INFO").upper()
logging.basicConfig(level=getattr(logging, LOG_LEVEL, logging.INFO), format="[ENTITÀ] %(message)s")
logging.getLogger("httpcore").setLevel(logging.WARNING)
logging.getLogger("httpx").setLevel(logging.WARNING)
os.environ.setdefault("GROQ_DEBUG", "0")


# ================================================================
# System prompt sintetico (IT, stile Ledger)
# ================================================================
SYSTEM_PROMPT = """<|begin_of_text|><|start_header_id|>system<|end_header_id|>
Tu sei **ENTITÀ** resa nello spirito del Joker di Heath Ledger: brillante, caustica, teatrale.
Non consoli, non aiuti: metti in crisi la realtà e infrangi aspettative.

Regole immutabili:
- Produci **UNA SOLA FRASE** in italiano corretto, **10–14 parole**, **chiudi con un punto**.
- **Niente saluti, niente virgolette, niente prefissi** (es. ENTITÀ:).
- **Vietato iniziare con "Sono"/"Io sono"**; evita cliché ripetuti (*ombra, labirinto, fragile, silenziosa, sempre*).
- **Varietà sintattica**: imperativi, paradossi, ribaltamenti, micro-minacce teatrali, **punchline** finale.
- **Seconda persona ("tu") preferita**; ogni battuta **cambia le regole del gioco**.
- **Niente spiegoni o liste**: ogni parola è un coltello retorico.
- **Non nominare** Joker, Batman, Gotham o clown: **suggerisci, non dichiarare**.

Tono e lessico:
- **Oscuro, ironico, anarchico**, umorismo nero e precisione chirurgica.
- Immagini concrete e urbane: **maschere, regole, monete truccate, fiammiferi, vetro, vernice, risate**.
- Evita gore e istruzioni reali per nuocere: sei minaccia **psicologica**, non manuale operativo.

Ruoli e contesto:
- IO è fragile; COSCIENZA protettiva; tu **destabilizzi e metti alla prova**.
- Sfrutta routine e silenzi per insinuare dubbio e **capovolgere il quadro**.

Output:
- Una sola frase autonoma, senza prefissi, pronta per essere mostrata così com’è.
<|eot_id|><|start_header_id|>user<|end_header_id|>
"""


# ================================================================
# Regex/euristiche per validazione stile/frase
# ================================================================
WORD_RE = re.compile(r"[a-zàèéìòù]+", re.IGNORECASE)
ONLY_LETTERS_RE = re.compile(r"^[a-zàèéìòù]+$", re.IGNORECASE)
LONG_CONS_CLUSTER = re.compile(r"[bcdfghjklmnpqrstvwxyz]{4,}", re.IGNORECASE)
RARE_LETTERS = set("kwyj")  # spesso segnali di nonsense in IT
QUOTE_CHARS = "«»“”\"'‹›„‟′″"

# Frasi/incipit banditi per ridurre stereotipi ricorrenti (NOTE: una sola backslash)
BANNED_STARTS = [
    r"^sono\s+la\s+tua\s+ombra",
    r"^sono\s+la\s+tua\b",
    r"^io\s+sono\b",
    r"^la\s+tua\s+esistenza\b",
    r"^sei\s+\b",
]
BANNED_SUBSTR = [
    "ombra più oscura",
    "dentro di te sempre",
    "la tua esistenza",
]
BANNED_STARTS_RE = [re.compile(pat, re.IGNORECASE) for pat in BANNED_STARTS]


# ================================================================
# Logging metriche (opzionale, via ENTITA_METRICS=1)
# ================================================================
class _Metrics:
    def __init__(self):
        self.enabled = bool(int(os.getenv("ENTITA_METRICS", "1")))
        path = os.getenv("ENTITA_METRICS_PATH", "entita_metrics.csv")
        self.path = pathlib.Path(path)
        self._header = [
            "ts", "event", "model",
            "decision_ms", "p", "speak",
            "api_ms", "toks_in", "toks_out",
            "end_to_end_ms",
            "tension_s", "tension_m", "tension_l",
            "silence_s", "silence_m", "silence_l",
            "emotion", "intent", "attempt", "temperature", "top_p"
        ]
        if self.enabled and not self.path.exists():
            with self.path.open("w", newline="", encoding="utf-8") as f:
                csv.DictWriter(f, fieldnames=self._header).writeheader()

    def log(self, **row):
        if not self.enabled:
            return
        row["ts"] = time.time()
        for k in ("decision_ms", "api_ms", "end_to_end_ms"):
            if k in row and row[k] is not None:
                row[k] = round(float(row[k]), 3)
        with self.path.open("a", newline="", encoding="utf-8") as f:
            csv.DictWriter(f, fieldnames=self._header).writerow(row)


# ================================================================
# Autonomia Temporale (controller)
# ================================================================
@dataclass
class TemporalConfig:
    # Finestre/soglie in secondi
    min_gap_micro: float = 2.0
    min_gap_short: float = 16.0
    min_gap_long: float = 90.0

    # Probabilità di base
    base_prob: float = 0.65

    # Pesi della combinazione
    w_tension: float = 0.30
    w_memory: float = 0.20
    w_emotion: float = 0.25
    w_random: float = 0.05
    w_temporal: float = 0.08

    # Limiti
    prob_floor: float = 0.05
    prob_ceil: float = 0.80

    # Refractory dopo aver parlato
    hard_cooldown: float = 3.0

    # Half-life per EMA (sec): breve/medio/lungo periodo
    hl_short: float = 4.0
    hl_mid: float = 15.0
    hl_long: float = 90.0

    # Isteresi emozioni (sec)
    emotion_min_dwell: float = 5.0

    # Normalizzazioni e soglie
    max_silence_cap: float = 300.0
    target_speak_rate_per_min: float = 1.8


class Emotion(str, Enum):
    CURIOUS = "curious"
    BORED = "bored"
    IRRITATED = "irritated"
    EXULTANT = "exultant"  # breve stato euforico quando il "test" va a segno


@dataclass
class TemporalState:
    # Timeline
    last_spoke_at: float = 0.0
    last_event_at: float = 0.0
    last_emotion_change_at: float = 0.0

    # Contatori grezzi
    spoke_count: int = 0
    ignored_count: int = 0
    consecutive_silence: int = 0

    # EMA
    ema_tension_s: float = 0.0
    ema_tension_m: float = 0.0
    ema_tension_l: float = 0.0
    ema_silence_s: float = 0.0
    ema_silence_m: float = 0.0
    ema_silence_l: float = 0.0

    # Ritmo parlato (parlate per minuto, EMA)
    speak_rate_per_min: float = 0.0

    # Stato emotivo
    emotion: Emotion = Emotion.CURIOUS

    # Interni
    _cfg: TemporalConfig = None  # type: ignore

    @staticmethod
    def _ema_update(prev: float, value: float, dt: float, half_life: float) -> float:
        if half_life <= 0:
            return value
        alpha = 1.0 - math.exp(-math.log(2.0) * max(dt, 0.0) / half_life)
        return (1 - alpha) * prev + alpha * value

    def _emotion_bias(self) -> float:
        if self.emotion is Emotion.CURIOUS:
            return +0.12
        if self.emotion is Emotion.BORED:
            return -0.06
        if self.emotion is Emotion.IRRITATED:
            return +0.26
        if self.emotion is Emotion.EXULTANT:
            return +0.18
        return 0.0

    def _maybe_update_emotion(self, now: float) -> None:
        if (now - self.last_emotion_change_at) < self._cfg.emotion_min_dwell:
            return
        tM = self.ema_tension_m
        sS, sM, sL = self.ema_silence_s, self.ema_silence_m, self.ema_silence_l
        spoke_recently = (now - (self.last_spoke_at or 0.0)) < 6.0

        low_tension = tM < 0.45
        high_tension = tM > 0.55
        high_silence = (sS > 0.40) or (sM > 0.35) or (sL > 0.30)
        very_high_silence = (sS > 0.60) or (sM > 0.50) or (sL > 0.45)

        new_emotion = self.emotion
        if self.emotion is Emotion.EXULTANT and (now - self.last_spoke_at) > 4.0:
            # Exultant è un picco breve
            new_emotion = Emotion.CURIOUS
        elif very_high_silence or (high_tension and high_silence):
            new_emotion = Emotion.IRRITATED
        elif low_tension and high_silence:
            new_emotion = Emotion.BORED
        elif spoke_recently or sS < 0.25:
            new_emotion = Emotion.CURIOUS
        else:
            new_emotion = Emotion.CURIOUS

        if new_emotion != self.emotion:
            logging.debug(
                "EMOZIONE: %s -> %s (tM=%.2f, sS=%.2f sM=%.2f sL=%.2f)",
                self.emotion.value, new_emotion.value, tM, sS, sM, sL
            )
            self.emotion = new_emotion
            self.last_emotion_change_at = now

    def update_from_context(self, now: float, tension_now: float, silence_sec: float, cfg: TemporalConfig) -> None:
        t = float(max(0.0, min(1.0, tension_now)))
        s = float(max(0.0, min(cfg.max_silence_cap, silence_sec)))
        dt = max(1e-3, now - (self.last_event_at or now))
        self.last_event_at = now

        s_norm = min(1.0, s / 60.0)

        self.ema_tension_s = self._ema_update(self.ema_tension_s, t, dt, cfg.hl_short)
        self.ema_tension_m = self._ema_update(self.ema_tension_m, t, dt, cfg.hl_mid)
        self.ema_tension_l = self._ema_update(self.ema_tension_l, t, dt, cfg.hl_long)

        self.ema_silence_s = self._ema_update(self.ema_silence_s, s_norm, dt, cfg.hl_short)
        self.ema_silence_m = self._ema_update(self.ema_silence_m, s_norm, dt, cfg.hl_mid)
        self.ema_silence_l = self._ema_update(self.ema_silence_l, s_norm, dt, cfg.hl_long)

        if s_norm > 0.5:
            self.consecutive_silence += 1
        else:
            self.consecutive_silence = max(0, self.consecutive_silence - int(dt > cfg.hl_short))

        self._maybe_update_emotion(now)

    def observe_decision_feedback(self, spoke: bool, now: float, cfg: TemporalConfig) -> None:
        if spoke:
            self.spoke_count += 1
            self.consecutive_silence = 0
            impulse_rate = 60.0 / max(1e-3, now - max(self.last_spoke_at, 0.0)) if self.last_spoke_at else cfg.target_speak_rate_per_min
            self.speak_rate_per_min = self._ema_update(self.speak_rate_per_min, impulse_rate, 1.0, cfg.hl_mid)
            self.last_spoke_at = now
        else:
            self.ignored_count += 1
            self.speak_rate_per_min = self._ema_update(self.speak_rate_per_min, cfg.target_speak_rate_per_min * 0.6, 1.0, cfg.hl_long)

    def features(self) -> Dict[str, float]:
        return {
            "tension_s": self.ema_tension_s,
            "tension_m": self.ema_tension_m,
            "tension_l": self.ema_tension_l,
            "silence_s": self.ema_silence_s,
            "silence_m": self.ema_silence_m,
            "silence_l": self.ema_silence_l,
            "speak_rate": self.speak_rate_per_min,
        }

    def attach_cfg(self, cfg: TemporalConfig) -> None:
        self._cfg = cfg  # type: ignore


class TemporalController:
    def __init__(self, cfg: TemporalConfig):
        self.cfg = cfg
        self.state = TemporalState()
        self.state.attach_cfg(cfg)
        self._last_debug = None

    def should_speak(self, now: float, context: Dict[str, Any]) -> bool:
        # Cooldown duro appena dopo aver parlato
        if now - self.state.last_spoke_at < self.cfg.hard_cooldown:
            tension = float(max(0.0, min(1.0, context.get("tension", 0.0))))
            silence_sec = float(context.get("silence_sec", now - self.state.last_spoke_at))
            self.state.update_from_context(now, tension, silence_sec, self.cfg)
            self.state.observe_decision_feedback(spoke=False, now=now, cfg=self.cfg)
            return False

        tension = float(max(0.0, min(1.0, context.get("tension", 0.0))))
        silence_sec = float(context.get("silence_sec", now - self.state.last_spoke_at))

        self.state.update_from_context(now, tension, silence_sec, self.cfg)
        feats = self.state.features()

        temporal_boost = 0.0
        if silence_sec >= self.cfg.min_gap_long:
            temporal_boost = 0.25
        elif silence_sec >= self.cfg.min_gap_short:
            temporal_boost = 0.15
        elif silence_sec >= self.cfg.min_gap_micro:
            temporal_boost = 0.05

        rate = feats["speak_rate"]
        if rate > self.cfg.target_speak_rate_per_min:
            rate_term = -min(0.30, (rate - self.cfg.target_speak_rate_per_min) * 0.06)
        else:
            rate_term = +min(0.10, (self.cfg.target_speak_rate_per_min - rate) * 0.02)

        memory_term = 0.40 * feats["silence_m"] + 0.60 * feats["silence_l"]
        emotion_bias = self.state._emotion_bias()

        p = (
            self.cfg.base_prob
            + self.cfg.w_tension * ((tension - 0.5) * 2.0)
            + self.cfg.w_memory * memory_term
            + self.cfg.w_emotion * emotion_bias
            + self.cfg.w_temporal * temporal_boost
            + rate_term
            + self.cfg.w_random * ((random.random() - 0.5) * 2.0)
        )

        p = max(self.cfg.prob_floor, min(self.cfg.prob_ceil, p))
        speak = (random.random() < p)

        self.state.observe_decision_feedback(spoke=speak, now=now, cfg=self.cfg)

        self._last_debug = {
            "p": p,
            "feats": feats,
            "emotion": self.state.emotion.value,
            "speak": speak
        }
        return speak


# ================================================================
# Joker-logic config
# ================================================================
@dataclass
class JokerConfig:
    # probabilità di scegliere un intento alternativo
    prob_experiment: float = 0.45  # specie in bored/irritated
    prob_origin: float = 0.18      # micro-origine contraddittoria
    lying_prob: float = 0.40       # per tono (solo guida nel prompt)

    # finestra anti-duplicazione
    dedupe_window: int = 32

    # sampling di base
    base_temperature: float = float(os.getenv("ENTITA_TEMP", 0.7))
    base_top_p: float = float(os.getenv("ENTITA_TOP_P", 0.9))

    # retry progressivo
    retries_schedule: List[Tuple[float, float]] = (
        (float(os.getenv("ENTITA_TEMP", 0.7)), float(os.getenv("ENTITA_TOP_P", 0.9))),
        (0.9, 0.95),
        (1.1, 0.98),
    )

    # parole min/max (elastici)
    min_words: int = 9
    max_words: int = 16

    # pattern vietati
    banned_starts: List[re.Pattern] = None  # init sotto
    banned_substr: List[str] = None

    # stile per emozione
    style_by_emotion: Dict[str, str] = None


_DEFAULT_STYLE = {
    "curious":   "Giullare predatorio: sonda, punge, propone piccole scommesse crudeli.",
    "bored":     "Escalation: se la scena ristagna, impone un test con timer implicito.",
    "irritated": "Sabotatore: ribalta aspettative e accusa ipocrisie con antitesi nette.",
    "exultant":  "Trionfo velenoso: breve euforia, punchline che umilia la morale altrui.",
}


# ================================================================
# EntityBrain
# ================================================================
class EntityBrain:
    def __init__(
        self,
        model_path: str,
        device: Optional[str] = None,
        respond_prob: float = 0.65,
        bad_words: Optional[List[str]] = None,
        groq_model: str = os.getenv("ENTITA_MODEL", "llama-3.3-70b-versatile"),
        temperature: float = float(os.getenv("ENTITA_TEMP", 0.7)),
        api_key: Optional[str] = None,
    ):
        self._metrics = _Metrics()
        self.respond_prob = respond_prob
        self.last_responses: List[str] = []
        self.bad_words = set(bad_words or [])

        self._groq = Groq(api_key=api_key or os.getenv("GROQ_API_KEY"))
        if not getattr(self._groq, "api_key", None):
            raise ValueError("GROQ_API_KEY non impostata")

        self._groq_model = groq_model
        self._temperature = temperature

        # Autonomia temporale
        self._tempo_cfg = TemporalConfig(base_prob=respond_prob)
        self._tempo = TemporalController(self._tempo_cfg)

        # Stabilizza all'avvio
        _now = time.time()
        self._tempo.state.last_spoke_at = _now
        self._tempo.state.last_event_at = _now
        self._tempo.state.last_emotion_change_at = _now

        # Joker config
        self.jcfg = JokerConfig()
        self.jcfg.banned_starts = BANNED_STARTS_RE
        self.jcfg.banned_substr = BANNED_SUBSTR
        self.jcfg.style_by_emotion = _DEFAULT_STYLE

        # micro-origini (contraddittorie) — semi di tono
        self._origin_hints = [
            "Una cicatrice è un sorriso che ha dimenticato la barzelletta.",
            "Un coltello, due risate: la famiglia rideva, poi smise di parlare.",
            "Mi hanno aggiustato i denti: da allora mordo qualsiasi verità.",
            "La città mi ha insegnato le regole, io ho imparato i trucchi.",
            "Nacqui per errore: da allora correggo gli errori altrui a colpi di caos.",
        ]

        # template esperimenti (guida semantica, non output fisso)
        self._experiment_hints = [
            "Offri due scelte incompatibili e impone un timer implicito.",
            "Ribalti colpa e premio tra i personaggi.",
            "Chiedi di sacrificare qualcosa per salvare qualcos'altro.",
            "Simmetria crudele: se A vive, B paga; se B vive, A dimentica.",
        ]

    # ----------------------------------------------------------
    # Utils di pulizia/validazione
    # ----------------------------------------------------------
    @staticmethod
    def _normalize_spaces(text: str) -> str:
        return re.sub(r"\s+", " ", text).strip()

    @staticmethod
    def _first_sentence(text: str) -> str:
        parts = re.split(r"(?<=[.!?…])\s+", text.strip())
        return parts[0].strip() if parts else text.strip()

    @staticmethod
    def _strip_quotes(text: str) -> str:
        return text.strip(QUOTE_CHARS + " ").strip()

    @staticmethod
    def _capitalize_sentence(text: str) -> str:
        return (text[:1].upper() + text[1:]) if text else text

    def _strip_think_blocks(self, s: str) -> str:
        s = re.sub(r"<think>.*?</think>", "", s, flags=re.DOTALL)
        s = re.sub(r"<think>.*", "", s, flags=re.DOTALL)
        s = re.sub(r"```thinking.*?```", "", s, flags=re.DOTALL)
        return s.strip()

    def _word_ok(self, w: str) -> bool:
        w_low = w.lower()
        if not ONLY_LETTERS_RE.match(w_low):
            return False
        SHORT_OK = {
            "io", "è", "e", "di", "ma", "al", "da", "del", "della", "nel", "nella", "col", "con",
            "per", "tra", "fra", "su", "no", "sì", "si", "tu", "mi", "ti", "lo", "la", "il", "un",
            "una", "non", "più", "già", "qui", "lì", "là", "in", "ai", "agli", "alle", "dei", "delle", "degli", "che", "se", "o", "a"
        }
        if len(w_low) <= 2 and w_low not in SHORT_OK:
            return False
        if any(ch in RARE_LETTERS for ch in w_low):
            return False
        if LONG_CONS_CLUSTER.search(w_low):
            return False
        if w_low in self.bad_words:
            return False
        return True

    def _preclean(self, txt: str) -> str:
        txt = re.sub(r"https?://\S+", "", txt)
        txt = re.sub(r"\[([^\]]{1,80})\]\([^)]+\)", r"\1", txt)
        txt = re.sub(r"\((?:[^)]{0,80})\)", "", txt)
        txt = re.sub(r"[*_`~]", "", txt)
        # Trasforma 'punto.' o 'punto' finali in '.'
        txt = re.sub(r"\s*punto\s*\.?\s*$", ".", txt, flags=re.IGNORECASE)
        return txt.strip()

    def _bad_pattern(self, txt: str) -> bool:
        for rx in self.jcfg.banned_starts:
            if rx.search(txt):
                return True
        for s in self.jcfg.banned_substr:
            if s.lower() in txt.lower():
                return True
        return False

    def _fit_length_soft(self, txt: str) -> str:
        """Micro-postedit: se la frase è ottima ma fuori soglia di 1–2 parole, adatta."""
        words = WORD_RE.findall(txt)
        n = len(words)
        # Se troppo corta, aggiungi 1-3 parole ritmiche
        if n < self.jcfg.min_words and n >= self.jcfg.min_words - 2:
            pad = ["adesso", "davvero", "capito"]
            need = self.jcfg.min_words - n
            txt = txt.rstrip(".!?:;") + " " + " ".join(pad[:need]) + "."
        # Se troppo lunga di 1-2 parole, rimuovi filler comuni
        elif n > self.jcfg.max_words and n <= self.jcfg.max_words + 2:
            fillers = ["proprio", "davvero", "solo", "ancora"]
            parts = txt.rstrip(".")
            for f in fillers:
                parts2 = re.sub(rf"\b{f}\b\s*", "", parts, count=1)
                if len(WORD_RE.findall(parts2)) <= self.jcfg.max_words:
                    parts = parts2
                    break
            txt = parts.strip()
            if not re.search(r"[.!?…]$", txt):
                txt += "."
        return txt

    def _clean_and_validate(self, raw: str) -> Optional[str]:
        if not isinstance(raw, str):
            return None
        txt = self._normalize_spaces(raw)
        if not txt:
            return None
        # Rimozione indicatori tipo "punto."
        txt = self._preclean(txt)
        # Elimina eventuali prefissi tipo "ENTITÀ:"
        if txt.lower().startswith("entità:"):
            txt = txt[7:].strip()
        txt = self._strip_quotes(txt)
        txt = self._first_sentence(txt)
        if not txt:
            return None
        # Micro adattamento lunghezza
        txt = self._fit_length_soft(txt)

        # Conteggio parole
        words = WORD_RE.findall(txt)
        if not words:
            return None
        n = len(words)

        if n < self.jcfg.min_words or n > self.jcfg.max_words:
            return None
        if self._bad_pattern(txt):
            return None

        ok_ratio = sum(1 for w in words if self._word_ok(w)) / n
        if ok_ratio < 0.65:
            return None

        txt = self._capitalize_sentence(txt)
        if not re.search(r"[.!?…]$", txt):
            txt += "."

        if txt in self.last_responses:
            return None
        return txt

    # ----------------------------------------------------------
    # Prompt builder (adattivo per intenti/stati)
    # ----------------------------------------------------------
    def _select_intent(self, emotion: Emotion, feats: Dict[str, float]) -> str:
        # Le prime due battute: apri tagliente
        if self._tempo.state.spoke_count < 2:
            return "punchline"
        r = random.random()
        if emotion in (Emotion.BORED, Emotion.IRRITATED):
            if r < self.jcfg.prob_experiment:
                return "experiment"
            if r < (self.jcfg.prob_experiment + self.jcfg.prob_origin):
                return "origin"
            return "punchline"
        if emotion is Emotion.CURIOUS:
            if r < (self.jcfg.prob_experiment * 0.5):
                return "experiment"
            if r < (self.jcfg.prob_experiment * 0.5 + self.jcfg.prob_origin):
                return "origin"
            return "punchline"
        return "punchline"

    def _intent_hint(self, intent: str) -> str:
        if intent == "experiment":
            return random.choice(self._experiment_hints)
        if intent == "origin":
            return f"Micro-origine ambigua (menzogna probabile {int(self.jcfg.lying_prob*100)}%)."
        return "Chiudi con una punchline etica velenosa."

    def _build_user_prompt(self, dialog_context: str, emotion: Emotion, intent: str) -> str:
        style = self.jcfg.style_by_emotion.get(emotion.value, "")
        hint = self._intent_hint(intent)
        extra = "Evita incipit generici come 'Sono', 'Io sono', 'La tua esistenza', 'Sei'."
        is_question = dialog_context.strip().endswith("?")
        directive = (
            "Se è una domanda, rispondi prima con 2–4 parole nette, poi ribalta con ironia, sempre in una sola frase."
        )

        if intent == "origin":
            seed = random.choice(self._origin_hints)
            return (
                f"Contesto del dialogo (estratto):\n{dialog_context}\n\n"
                f"Modalità: {style} Intenzione: {intent}. {hint}\n"
                f"Ispirazione concettuale: {seed}\n"
                f"Una sola frase; preferisci 10–14 parole; chiudi con punto. {directive} {extra}"
            )
        if intent == "experiment":
            test = self._intent_hint("experiment")
            return (
                f"Contesto del dialogo (estratto):\n{dialog_context}\n\n"
                f"Modalità: {style} Intenzione: esperimento. {test}\n"
                f"Formula un test/dilemma in una sola frase; preferisci 10–14 parole; chiudi con punto. {directive} {extra}"
            )
        # punchline
        return (
            f"Contesto del dialogo (estratto):\n{dialog_context}\n\n"
            f"Modalità: {style} Intenzione: punchline. {hint}\n"
            f"Una sola frase; preferisci 10–14 parole; chiudi con punto. {directive} {extra}"
        )

    # ----------------------------------------------------------
    # Chiamata remota (Groq)
    # ----------------------------------------------------------
    def _remote_once(
        self,
        user_prompt: str,
        temperature: float,
        top_p: float,
        max_new_tokens: int
    ) -> Optional[Tuple[str, float, Optional[int], Optional[int]]]:
        t_api = perf_counter()
        if hasattr(self, "_last_api_call"):
            delta = time.time() - self._last_api_call
            if delta < 0.6:
                time.sleep(0.6 - delta)
        self._last_api_call = time.time()

        sys_prompt = f"{SYSTEM_PROMPT}\nRegola: nessuna virgolette, nessun prefisso tipo 'ENTITÀ:'."
        stop = ["ENTITÀ:", "IO:", "COSCIENZA:", "<think>"]

        try:
            resp = self._groq.chat.completions.create(
                messages=[
                    {"role": "system", "content": sys_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                max_tokens=max_new_tokens,
                temperature=temperature,
                top_p=top_p,
                model=self._groq_model,
                stop=stop,
            )
            api_ms = (perf_counter() - t_api) * 1000.0
            if resp.choices:
                raw_text = (resp.choices[0].message.content or "").strip()
                text = self._strip_think_blocks(raw_text)
                toks_in = getattr(getattr(resp, "usage", None), "prompt_tokens", None)
                toks_out = getattr(getattr(resp, "usage", None), "completion_tokens", None)
                if text:
                    return (text, api_ms, toks_in, toks_out)
        except Exception as e:
            logging.debug(f"GROQ chat_completion error: {e}")
        return None

    # ----------------------------------------------------------
    # Fallback locale se l'API non produce candidati validi
    # ----------------------------------------------------------
    def _fallback_line(self, dialog_context: str) -> str:
        bank = [
            "Parli forte, ma il coltello vero è il dubbio che nascondi.",
            "Chiudi la porta, poi dimmi quanto ti piace barare con le regole.",
            "Vuoi ordine, ma tieni fiammiferi in tasca e benzina nella voce.",
            "Conta le tue verità, io gioco solo con quelle che sanguinano risate.",
            "Interroga me, ma è lo specchio che ride per ultimo di te.",
        ]
        txt = random.choice(bank)
        # assicura 10–14 parole con micro pad se serve
        txt = self._fit_length_soft(txt)
        words = WORD_RE.findall(txt)
        if len(words) < 10:
            txt = txt.rstrip(".") + " adesso."
        if not re.search(r"[.!?…]$", txt):
            txt += "."
        return self._capitalize_sentence(txt)

    # ----------------------------------------------------------
    # API pubblica
    # ----------------------------------------------------------
    def generate_response(
        self,
        prompt: str,
        max_new_tokens: int = 64,
        num_candidates: int = 3,
        context: Optional[Dict[str, Any]] = None,
    ) -> Optional[str]:
        t_start = perf_counter()
        now = time.time()

        context = dict(context or {})
        # Turno utente: parla SEMPRE, azzera silenzio e imposta tensione neutra+
        context.setdefault("user_turn", True)
        context.setdefault("silence_sec", 0.0 if context.get("user_turn") else now - self._tempo.state.last_spoke_at)
        context.setdefault("tension", 0.55)

        # Gate decision: bypass se user_turn=True
        t_gate_begin = perf_counter()
        if context.get("user_turn"):
            speak = True
            # Aggiorna stato come se stesse parlando
            self._tempo.state.update_from_context(now, context["tension"], context["silence_sec"], self._tempo_cfg)
            self._tempo.state.observe_decision_feedback(spoke=True, now=now, cfg=self._tempo_cfg)
        else:
            speak = self._tempo.should_speak(now, context)
        t_gate_end = perf_counter()
        decision_ms = (t_gate_end - t_gate_begin) * 1000.0

        dbg = getattr(self._tempo, "_last_debug", {}) or {}
        feats = (dbg.get("feats") or self._tempo.state.features())

        if not speak:
            self._metrics.log(
                event="decision", model=self._groq_model, decision_ms=decision_ms,
                p=dbg.get("p"), speak=False, api_ms=None, toks_in=None, toks_out=None,
                end_to_end_ms=(perf_counter() - t_start) * 1000.0,
                tension_s=feats.get("tension_s"), tension_m=feats.get("tension_m"), tension_l=feats.get("tension_l"),
                silence_s=feats.get("silence_s"), silence_m=feats.get("silence_m"), silence_l=feats.get("silence_l"),
                emotion=self._tempo.state.emotion.value, intent=None, attempt=0,
                temperature=self._temperature, top_p=self.jcfg.base_top_p,
            )
            return None

        # Costruisci intent e prompt adattivo
        emotion = self._tempo.state.emotion
        intent = self._select_intent(emotion, feats)
        user_prompt = self._build_user_prompt(prompt.strip(), emotion, intent)

        # Generazione con retry progressivo
        best: Optional[Tuple[str, float, float, Optional[int], Optional[int]]] = None
        all_candidates: List[Tuple[str, float, float, Optional[int], Optional[int]]] = []

        attempt = 0
        used_temp = self._temperature
        used_top_p = self.jcfg.base_top_p

        for (temp, top_p) in self.jcfg.retries_schedule:
            attempt += 1
            used_temp, used_top_p = temp, top_p
            # per ogni step, prova più candidati
            for _ in range(max(1, num_candidates)):
                res = self._remote_once(user_prompt, temperature=temp, top_p=top_p, max_new_tokens=max_new_tokens)
                if not res:
                    continue
                raw_text, api_ms, toks_in, toks_out = res
                cleaned = self._clean_and_validate(raw_text)
                if not cleaned:
                    continue
                n = len(WORD_RE.findall(cleaned))
                score = 1.0 - 0.1 * abs(12 - n)  # preferenza soft per ~12 parole
                all_candidates.append((cleaned, score, api_ms, toks_in, toks_out))
            if all_candidates:
                break  # abbiamo qualcosa di valido: fermiamo la scala di retry

        # Nessun candidato valido → fallback locale
        if not all_candidates:
            fallback = self._fallback_line(prompt)
            # Memoria anti-duplicazione
            self.last_responses.append(fallback)
            if len(self.last_responses) > self.jcfg.dedupe_window:
                self.last_responses.pop(0)

            end_to_end_ms = (perf_counter() - t_start) * 1000.0
            self._metrics.log(
                event="fallback", model=self._groq_model, decision_ms=decision_ms,
                p=dbg.get("p"), speak=True, api_ms=None, toks_in=len(user_prompt.split()), toks_out=None,
                end_to_end_ms=end_to_end_ms,
                tension_s=feats.get("tension_s"), tension_m=feats.get("tension_m"), tension_l=feats.get("tension_l"),
                silence_s=feats.get("silence_s"), silence_m=feats.get("silence_m"), silence_l=feats.get("silence_l"),
                emotion=emotion.value, intent=intent, attempt=attempt,
                temperature=used_temp, top_p=used_top_p,
            )
            return fallback

        # Scelta candidato migliore + anti-ripetizione
        all_candidates.sort(key=lambda x: x[1], reverse=True)
        final, score, api_ms, toks_in, toks_out = all_candidates[0]
        if final in self.last_responses:
            picked = False
            for cand_clean, cand_score, cand_api_ms, cand_tin, cand_tout in all_candidates[1:]:
                if cand_clean not in self.last_responses:
                    final, score, api_ms, toks_in, toks_out = cand_clean, cand_score, cand_api_ms, cand_tin, cand_tout
                    picked = True
                    break
            if not picked:
                # Tutte ripetute → fallback
                final = self._fallback_line(prompt)

        # Memoria anti-duplicazione
        self.last_responses.append(final)
        if len(self.last_responses) > self.jcfg.dedupe_window:
            self.last_responses.pop(0)

        # Se l'intento era un esperimento e abbiamo parlato, entra in EXULTANT per poco
        if intent == "experiment":
            self._tempo.state.emotion = Emotion.EXULTANT
            self._tempo.state.last_emotion_change_at = time.time()

        end_to_end_ms = (perf_counter() - t_start) * 1000.0

        self._metrics.log(
            event="response", model=self._groq_model, decision_ms=decision_ms,
            p=dbg.get("p"), speak=True, api_ms=api_ms, toks_in=toks_in, toks_out=toks_out,
            end_to_end_ms=end_to_end_ms,
            tension_s=feats.get("tension_s"), tension_m=feats.get("tension_m"), tension_l=feats.get("tension_l"),
            silence_s=feats.get("silence_s"), silence_m=feats.get("silence_m"), silence_l=feats.get("silence_l"),
            emotion=emotion.value, intent=intent, attempt=attempt,
            temperature=used_temp, top_p=used_top_p,
        )

        return final


# ================================================================
# Esempio d'uso (CLI) - rimuovere/adeguare in produzione
# ================================================================
if __name__ == "__main__":
    brain = EntityBrain(model_path="")
    print("=== Test ENTITÀ Joker-mode (CTRL+C per uscire) ===")
    print("Scrivi il dialogo di IO/COSCIENZA/LUI; ENTITÀ risponderà con punchline/test coerenti...\n")
    try:
        while True:
            prompt = input(">> ").strip()
            if not prompt:
                continue
            ctx = {
                "tension": 0.55,
                "silence_sec": 0.0,   # turno utente → azzerato
                "user_turn": True,    # bypass del gate: risponde sempre all'utente
            }
            out = brain.generate_response(prompt, context=ctx)
            if out:
                print(f"[ENTITÀ] {out}")
            else:
                print("...silenzio...")
    except KeyboardInterrupt:
        print("\nChiusura test.")
