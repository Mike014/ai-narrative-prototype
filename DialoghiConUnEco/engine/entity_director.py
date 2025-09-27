# engine/entity_director.py
# -*- coding: utf-8 -*-
"""
EntityDirector: 'regista' esterno che legge il dialogo (IO+COSCIENZA),
stima canali emotivi e decide interventi (audio/visual/toast/note).
NON aggiunge battute nel DialogManager.

Env utili:
- ENT_NOTE_ENABLED (1)        : abilita scrittura note
- ENT_NOTE_DIR                : cartella della nota (default Desktop)
- ENT_NOTE_BASENAME           : nome file (default eco_nota.txt)
- ENT_NOTE_OPEN_SECS          : secondi di apertura Notepad (default 2.5)
- ENT_CLEAR_NOTE_ON_START (1) : cancella nota all'avvio (una volta)
- ENT_OS_TOAST_ENABLED (0)    : abilita toast OS
- ENT_TOAST_PROB (0.25)       : probabilità toast
- ENT_TOAST_COOLDOWN (8.0)    : cooldown minimo tra toast (sec)
- ENT_TOAST_DEDUPE_WINDOW (30): finestra anti-duplicati per testo (sec)
- ENT_OPEN_NOTE_ON_TOAST (1)  : apre la nota quando fa un toast e iconifica il gioco
- ENT_ICONIFY_ON_TOAST (1)    : minimizza il gioco dopo aver aperto la nota
- ENT_CAPTION_PROB (0.25)
- HF_ENABLED (0), HF_MODEL_ID, HUGGINGFACE_API_KEY
- ENT_ICON_PATH               : path esplicito per l'icona delle notifiche (override)
"""

import os, re, json, time, random, logging, platform, subprocess, tempfile
from pathlib import Path
from typing import Dict, Optional, List, Tuple

import pygame

# Keras opzionale
try:
    from tensorflow.keras.models import load_model
    from tensorflow.keras.preprocessing.sequence import pad_sequences
    from tensorflow.keras.preprocessing.text import tokenizer_from_json
    TF_OK = True
except Exception:
    TF_OK = False

log = logging.getLogger(__name__)
WORD = re.compile(r"[a-zàèéìòù]+", re.IGNORECASE)


def _bool_env(name: str, default: bool) -> bool:
    v = os.getenv(name)
    if v is None:
        return default
    return v.strip().lower() in {"1", "true", "yes", "on"}


def _float_env(name: str, default: float) -> float:
    v = os.getenv(name)
    if v is None:
        return default
    try:
        return float(v)
    except Exception:
        return default


class EntityDirector:
    _CLEARED_ONCE = False  # cancella il file una volta per run

    def __init__(self, asset_func, model_name="entity_director.h5", tok_name="entity_director_tok.json"):
        """
        asset_func: funzione tipo project_path(*parts) che ritorna uno string path dalla root del progetto.
        """
        self.asset = asset_func

        # Config nota/toast
        self.allow_desktop_note = _bool_env("ENT_NOTE_ENABLED", True)
        note_dir_env = os.getenv("ENT_NOTE_DIR", "").strip()
        self.note_dir: Optional[Path] = Path(note_dir_env) if note_dir_env else None
        self.note_basename = os.getenv("ENT_NOTE_BASENAME", "eco_nota.txt")
        self.note_open_secs = _float_env("ENT_NOTE_OPEN_SECS", 2.5)
        self.clear_note_on_start = _bool_env("ENT_CLEAR_NOTE_ON_START", True)

        self.toasts_enabled = _bool_env("ENT_OS_TOAST_ENABLED", False)
        self.toast_prob = _float_env("ENT_TOAST_PROB", 0.050)  # probabilità toast opzionale
        self.toast_cooldown = _float_env("ENT_TOAST_COOLDOWN", 8.0)  # cooldown minimo tra toast (sec)
        self.toast_dedupe_window = _float_env("ENT_TOAST_DEDUPE_WINDOW", 30.0)
        self.open_note_on_toast = _bool_env("ENT_OPEN_NOTE_ON_TOAST", True)
        self._last_toast_time = 0.0
        self._recent_msgs: List[Tuple[str, float]] = []  # [(hash, ts)]

        # Caption (scrive su nota)
        self.caption_prob = _float_env("ENT_CAPTION_PROB", 0.25)
        self.caption_cooldown = 2.0
        self.last_caption_time = 0.0

        # HF
        self.hf_enabled = _bool_env("HF_ENABLED", False)
        self.hf_model_id = os.getenv("HF_MODEL_ID", "mistralai/Mixtral-8x7B-Instruct-v0.1")
        self.hf_client = None

        # Gestione Notepad
        self.note_proc: Optional[subprocess.Popen] = None
        self._note_close_at = 0.0

        # Pulisci file una volta
        if self.clear_note_on_start and not EntityDirector._CLEARED_ONCE:
            p = self._desktop_note_path()
            try:
                if p.exists():
                    p.unlink()
                EntityDirector._CLEARED_ONCE = True
            except Exception as e:
                log.warning("[EntityDirector] Impossibile cancellare nota all'avvio: %s", e)

        # Keras opzionale
        self.model = None
        self.tok = None
        if TF_OK:
            try:
                mp = self.asset("models", model_name)
                tp = self.asset("models", tok_name)
                if os.path.exists(mp) and os.path.exists(tp):
                    self.model = load_model(mp)
                    with open(tp, "r", encoding="utf-8") as f:
                        self.tok = tokenizer_from_json(json.load(f))
                else:
                    log.info("[EntityDirector] Modello/tokenizer non trovati: fallback.")
            except Exception as e:
                log.warning("[EntityDirector] Errore Keras: %s", e)

        try:
            if not pygame.font.get_init():
                pygame.font.init()
            self.toast_font = pygame.font.SysFont("consolas", 20)
        except Exception:
            self.toast_font = None

        # Icona per le notifiche (logo scena intro)
        self.app_icon_path = self._resolve_app_icon()

    # ------------------------------------------------------------------ ICONA --
    def _resolve_app_icon(self) -> Optional[str]:
        """
        Prova a usare l'icona del logo dell'intro:
        - ENT_ICON_PATH (se impostata) vince su tutto.
        - Su Windows preferisce .ico (logo.ico).
        - Su Linux/macOS vanno bene png/jpg.
        - Se su Windows non trovi .ico e c'è Pillow, converte al volo png/jpg a .ico temporanea.
        """
        env_icon = os.getenv("ENT_ICON_PATH", "").strip()
        if env_icon and os.path.exists(env_icon):
            return env_icon

        # Candidati .ico (Windows)
        candidates_ico = [
            self.asset("assets", "background", "logo.ico"),
            self.asset("assets", "icons", "logo.ico"),
            self.asset("assets", "icons", "app.ico"),
        ]
        for p in candidates_ico:
            if os.path.exists(p):
                return p

        # Immagini comuni
        img_candidates = [
            self.asset("assets", "background", "logo.png"),
            self.asset("assets", "background", "logo.jpg"),
            self.asset("assets", "background", "logo.jpeg"),
            self.asset("assets", "background", "logo_what_am_i.PNG"),
        ]

        # Non-Windows: png/jpg ok
        if platform.system() != "Windows":
            for p in img_candidates:
                if os.path.exists(p):
                    return p
            return None

        # Windows: serve .ico; prova conversione via Pillow se disponibile
        for p in img_candidates:
            if os.path.exists(p):
                try:
                    from PIL import Image  # opzionale
                    ico_tmp = Path(tempfile.gettempdir()) / "dialoghi_logo_tmp.ico"
                    img = Image.open(p).convert("RGBA")
                    img.save(
                        ico_tmp,
                        format="ICO",
                        sizes=[(256, 256), (128, 128), (64, 64), (32, 32), (16, 16)],
                    )
                    if ico_tmp.exists():
                        return str(ico_tmp)
                except Exception:
                    pass
                break  # tenta solo sul primo valido
        return None

    # --------------------------------------------------------------- SCORING --
    def _score_with_model(self, text: str) -> Dict[str, float]:
        seq = pad_sequences(self.tok.texts_to_sequences([text]), maxlen=96)
        y = self.model.predict(seq, verbose=0)[0]
        return {
            "tensione": float(y[0]),
            "oppressione": float(y[1]),
            "nostalgia": float(y[2]),
            "ruminazione": float(y[3]),
        }

    def _score_fallback(self, text: str) -> Dict[str, float]:
        t = text.lower()

        def score(keys):
            return float(min(1.0, sum(0.3 for k in keys if k in t)))

        return {
            "tensione": score(
                ["acufene", "metal", "premere", "tempia", "pianto", "scuro", "grigio", "puzzo", "vuoto", "lamento"]
            ),
            "oppressione": score(["pancia in giù", "oppress", "ferita", "trauma", "peso", "scuro", "vuoto"]),
            "nostalgia": score(["lei", "collana", "braccialetto", "ricordo", "loop", "tema", "accordi", "la maggiore"]),
            "ruminazione": score(["sarei", "ossessione", "pensavo", "dimenticare", "come posso", "perché"]),
        }

    def score_channels(self, dialog_text: str) -> Dict[str, float]:
        if self.model is not None and self.tok is not None:
            try:
                return self._score_with_model(dialog_text)
            except Exception as e:
                log.warning("[EntityDirector] Errore inferenza Keras: %s", e)
        return self._score_fallback(dialog_text)

    # --------------------------------------------------------------- CAPTION --
    def make_caption(self, chans: Dict[str, float]) -> Optional[str]:
        now = time.time()
        if now - self.last_caption_time < self.caption_cooldown:
            return None
        if random.random() > self.caption_prob:
            return None
        self.last_caption_time = now

        t, o, n, r = chans["tensione"], chans["oppressione"], chans["nostalgia"], chans["ruminazione"]
        candidates: List[str] = []
        if t > 0.6 and o > 0.6:
            candidates += [
                "La tempia pulsa: il corpo ricorda quello che la mente nega.",
                "Il respiro si spezza: la stanza si restringe attorno al dolore.",
                "Le vene battono contro il silenzio: ogni pulsazione è LEI.",
                "Il peso si accumula dove la pelle incontra il vuoto.",
                "Gli occhi bruciano di una luce che non è mai stata mia.",
                "Il dolore mappa territori che credevo sepolti.",
                "La fronte si contrae: sta decifrando un linguaggio perduto.",
            ]
        if n > 0.5:
            candidates += [
                "Gli oggetti custodiscono quello che LEI non ha mai restituito.",
                "La melodia non cura: riapre cucendo i bordi della ferita.",
                "I suoni si addensano: diventano il corpo che LEI non ha mai avuto.",
                "Ogni nota è una porta verso stanze che LEI non abiterà mai.",
                "L'eco ritorna vuota: porta il sapore di quello che non è stato.",
                "Le parole non dette a LEI gridano più forte di quelle pronunciate.",
                "Il rumore scava attraverso le crepe del pensiero.",
                "La musica implode: resta solo il vuoto che risuona.",
            ]
        if r > 0.5:
            candidates += [
                "Le domande su LEI tornano a spirale: più scavo, più affondano.",
                "Il pensiero lucida la stessa ferita finché sanguina.",
                "La mente gira intorno al vuoto che ho chiamato LEI.",
                "Ogni risposta su LEI genera tre nuove domande che bruciano.",
                "Il dubbio su LEI si nutre di sé: cresce affamato di certezze.",
                "I pensieri su LEI si rincorrono in cerchi sempre più stretti.",
                "La logica si spezza contro quello che il cuore già sapeva di LEI.",
                "Le certezze su LEI si sciolgono: resta solo il gusto amaro del forse.",
            ]
        if not candidates:
            candidates = [
                "La stanza tace, ma il corpo urla il nome di LEI.",
                "Ogni pausa è LEI che non risponde: ascolta il vuoto che lascia.",
                "Il vuoto ha il sapore di LEI: pesa più delle sue parole mai dette.",
                "Tra un respiro e l'altro vive tutto quello che LEI non è stata.",
                "La quiete vibra del suo silenzio: tutto quello che LEI non ha detto.",
                "Il tempo si addensa negli angoli dove LEI non è mai stata.",
                "Anche il nulla sa di LEI: sa di attesa e di pelle mai toccata.",
                "Le ombre danzano LEI: storie che la luce non ha mai illuminato.",
            ]
        self.queue_fake_toast(random.choice(candidates))
        return None

    # -------------------------------------------------------------- DEDUPE ----
    def _suppress_repeated(self, text: str) -> bool:
        now = time.time()
        cutoff = now - self.toast_dedupe_window
        self._recent_msgs = [(h, t) for (h, t) in self._recent_msgs if t >= cutoff]
        h = str(hash(text))
        for (hh, _) in self._recent_msgs:
            if hh == h:
                return True
        self._recent_msgs.append((h, now))
        if len(self._recent_msgs) > 64:
            self._recent_msgs = self._recent_msgs[-64:]
        return False

    # ----------------------------------------------------------- TOAST/NOTE ---
    def queue_fake_toast(self, text: str, dialog_context: Optional[str] = None, ms: int = 1800):
        now = time.time()
        if now - self._last_toast_time < self.toast_cooldown:
            return
        if self._suppress_repeated(text):
            return

        # Scrivi su file prima (così la nota mostra anche questo contenuto)
        note_path = self.write_desktop_note(text)

        will_open_and_iconify = bool(self.open_note_on_toast and note_path)

        opened_ok = False
        if will_open_and_iconify:
            opened_ok = self._open_note_brief(note_path)

        if opened_ok:
            # Mostra sempre una notifica visibile, con icona se disponibile
            self._guaranteed_notify(text, ms=ms)

        if _bool_env("ENT_ICONIFY_ON_TOAST", True) and opened_ok:
            try:
                pygame.display.iconify()
            except Exception as e:
                log.info("[EntityDirector] Iconify fallito: %s", e)
        else:
            # Ramo opzionale: toast OS (senza iconify) governato da probabilità
            if self.toasts_enabled and random.random() < self.toast_prob:
                try:
                    from plyer import notification
                    icon_kw = {}
                    if self.app_icon_path:
                        icon_kw["app_icon"] = self.app_icon_path
                    notification.notify(
                        title="Dialoghi con un'Eco",
                        message=text,
                        timeout=max(1, int(ms / 1000)),
                        **icon_kw,
                    )
                except Exception as e:
                    log.info("[EntityDirector] Toast OS non disponibile: %s", e)
                if platform.system() == "Windows":
                    # Fallback best-effort
                    try:
                        import ctypes, threading

                        def _box():
                            ctypes.windll.user32.MessageBoxW(0, text, "Dialoghi con un'Eco", 0x40)  # MB_ICONINF

                        threading.Thread(target=_box, daemon=True).start()
                    except Exception as e2:
                        log.info("[EntityDirector] MessageBox fallback fallito: %s", e2)

            # Eventuale risposta modello (opzionale)
            if dialog_context and self.hf_enabled:
                try:
                    self.write_model_response(dialog_context)
                except Exception as e:
                    log.warning("[EntityDirector] Errore HF: %r", e)

        self._last_toast_time = now

    # --- apertura/chiusura Notepad (robusta per Windows 10/11) ---
    def _open_note_brief(self, path: Path):
        # se c'è una finestra precedente, la chiudo subito (per refresh/timer)
        self._maybe_close_note(force=True)
        try:
            if platform.system() == "Windows":
                import ctypes
                si = subprocess.STARTUPINFO()
                si.dwFlags |= subprocess.STARTF_USESHOWWINDOW
                si.wShowWindow = ctypes.c_int(3)  # SW_MAXIMIZE
                self.note_proc = subprocess.Popen(["notepad.exe", str(path)], startupinfo=si)
            elif platform.system() == "Darwin":
                self.note_proc = subprocess.Popen(["open", str(path)])
            else:
                self.note_proc = subprocess.Popen(["xdg-open", str(path)])
        except Exception as e:
            log.info("[EntityDirector] Impossibile aprire nota: %s", e)
            self.note_proc = None
            return False

        self._note_close_at = time.time() + max(1.5, float(self.note_open_secs))
        return True

    def _close_note_windows_robust(self):
        """Chiude la finestra di Notepad legata al file (Windows 10/11, anche nuova app)."""
        basename = self._desktop_note_path().name
        ps = (
            "powershell -NoProfile -Command "
            "$n='{name}';"
            "$procs=Get-Process | Where-Object {{$_.MainWindowTitle -like \"*${{n}}*\"}};"
            "foreach($p in $procs) {{"
            "  $null=$p.CloseMainWindow(); Start-Sleep -Milliseconds 200;"
            "  if(-not $p.HasExited) {{ Stop-Process -Id $p.Id -Force }};"
            "}}"
        ).format(name=basename)
        try:
            subprocess.Popen(ps, shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        except Exception as e:
            log.info("[EntityDirector] PowerShell close fallback failed: %s", e)

    def _maybe_close_note(self, force: bool = False):
        # su piattaforme non Windows non possiamo garantire la chiusura
        if platform.system() != "Windows":
            self.note_proc = None
            return

        # 1) se avevamo un Popen e il PID è vivo, prova terminate/kill per PID
        if self.note_proc is not None and self.note_proc.poll() is None:
            if force or time.time() >= self._note_close_at:
                try:
                    self.note_proc.terminate()
                    time.sleep(0.1)
                    if self.note_proc.poll() is None:
                        subprocess.Popen(
                            ["taskkill", "/PID", str(self.note_proc.pid), "/F"],
                            stdout=subprocess.DEVNULL,
                            stderr=subprocess.DEVNULL,
                        )
                except Exception as e:
                    log.info("[EntityDirector] terminate/kill PID fallito: %s", e)
                finally:
                    self.note_proc = None

        # 2) chiusura robusta per titolazione finestra (nuovo Notepad/UWP)
        if force or time.time() >= self._note_close_at:
            self._close_note_windows_robust()
            self.note_proc = None  # disaccoppia comunque

    # --------------------------------------------------------------- HF OPT. ---
    def __init_hf_client(self):
        if not self.hf_enabled:
            raise RuntimeError("HF non abilitato (HF_ENABLED=False)")
        if self.hf_client is not None:
            return
        from huggingface_hub import InferenceClient

        tok = os.getenv("HUGGINGFACE_API_KEY")
        if not tok:
            raise ValueError("HUGGINGFACE_API_KEY non impostata")
        self.hf_client = InferenceClient(self.hf_model_id, token=tok)

    def write_model_response(self, dialog_context: str):
        if not self.hf_enabled:
            raise RuntimeError("HF non abilitato (HF_ENABLED=False)")
        try:
            self.__init_hf_client()
            sys_prompt = (
                "Tu sei ENTITÀ. Rispondi in modo crudele, una sola frase, tra 10 e 14 parole, "
                "senza virgolette né prefissi, termina con punto."
            )
            resp = self.hf_client.chat_completion(
                messages=[{"role": "system", "content": sys_prompt}, {"role": "user", "content": dialog_context}],
                max_tokens=32,
                temperature=0.78,
                top_p=0.9,
                model=self.hf_model_id,
            )
            if hasattr(resp, "choices") and resp.choices:
                text = (resp.choices[0].message.get("content", "") or "").strip()
            else:
                text = str(resp).strip()
            p = self._desktop_note_path()
            with open(p, "a", encoding="utf-8") as f:
                f.write("\n[ENTITÀ] " + text + "\n")
        except Exception as e:
            log.warning("[EntityDirector] Errore HF: %r", e)
            try:
                p = self._desktop_note_path()
                with open(p, "a", encoding="utf-8") as f:
                    f.write(f"\n[ERRORE MODELLO] {repr(e)}\n")
            except Exception as fe:
                log.warning("[EntityDirector] Errore scrittura errore modello: %s", fe)

    # ------------------------------------------------------------- DESKTOP NOTE
    def _desktop_note_path(self) -> Path:
        if self.note_dir:
            self.note_dir.mkdir(parents=True, exist_ok=True)
            return self.note_dir / self.note_basename
        desktop = Path(os.environ.get("USERPROFILE", "")) / "Desktop"
        if not desktop.exists():
            desktop = Path.home() / "Desktop"
        return desktop / self.note_basename

    def write_desktop_note(self, text: str) -> Optional[Path]:
        if not self.allow_desktop_note:
            return None
        try:
            p = self._desktop_note_path()
            with open(p, "a", encoding="utf-8") as f:
                f.write(text.strip() + "\n")
            return p
        except Exception as e:
            log.warning("[EntityDirector] Impossibile scrivere nota: %s", e)
            return None

    # ----------------------------------------------------- NOTIFY GARANTITA ---
    def _guaranteed_notify(self, text: str, ms: int = 1800) -> None:
        """Mostra SEMPRE una notifica visibile quando stiamo per iconify.
        Ignora ENT_OS_TOAST_ENABLED, probabilità e cooldown.
        Usa l'icona del logo se disponibile.
        """
        try:
            from plyer import notification

            icon_kw = {}
            if self.app_icon_path:
                icon_kw["app_icon"] = self.app_icon_path

            notification.notify(
                title="Dialoghi con un'Eco",
                message=text,
                timeout=max(1, int(ms / 1000)),
                **icon_kw,
            )
            return
        except Exception as e:
            log.info("[EntityDirector] Toast OS non disponibile: %s", e)

        # Fallback Windows: MessageBox (senza icona personalizzata)
        try:
            if platform.system() == "Windows":
                import ctypes

                ctypes.windll.user32.MessageBoxW(0, text, "Dialoghi con un'Eco", 0x40)
                # second box non bloccante
                def _box():
                    ctypes.windll.user32.MessageBoxW(0, text, "Dialoghi con un'Eco", 0x40)  # MB_ICONINF

                import threading

                threading.Thread(target=_box, daemon=True).start()
        except Exception as e2:
            log.info("[EntityDirector] MessageBox fallback fallito: %s", e2)

    # ---------------------------------------------------------- TICK/MAINT ----
    def draw_fake_toasts(self, screen):
        self._maybe_close_note(force=False)
        return

    # -------------------------------------------------------------- UTILITY ---
    @staticmethod
    def open_path_crossplatform(path: Path):
        try:
            if platform.system() == "Windows":
                try:
                    subprocess.Popen(["notepad.exe", str(path)])
                except Exception:
                    os.startfile(str(path))  # type: ignore[attr-defined]
            elif platform.system() == "Darwin":
                subprocess.Popen(["open", str(path)])
            else:
                subprocess.Popen(["xdg-open", str(path)])
        except Exception as e:
            log.info("[EntityDirector] Open path error: %s", e)
