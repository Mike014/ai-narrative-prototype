# -*- coding: utf-8 -*-
"""
ENTITÀ TTS — riproduzione 'as-is' della tua voce ElevenLabs
Usabile sia da CLI (per test) che come modulo nelle scene (tts_to_file / ensure_cached_tts).
"""

from __future__ import annotations
import os
import sys
import pathlib
from typing import Optional

from elevenlabs.client import ElevenLabs
from elevenlabs.play import play
from elevenlabs.core.api_error import ApiError

# ---------------------------------------------------------------------------
# Config di default (puoi sovrascrivere via variabili d'ambiente)
# ---------------------------------------------------------------------------

API_KEY: Optional[str] = (
    os.getenv("ELEVEN_API_KEY")
    or os.getenv("XI_API_KEY")
    or os.getenv("ELEVENLABS_API_KEY")
)

# La tua voce ENTITÀ
VOICE_ID: str = os.getenv("ENTITA_VOICE_ID", "i9qjWtU9ESfMXufwwLOm")

# Il modello del preview che stai usando nella UI.
# Se non hai accesso a v3 via API, cambia in "eleven_multilingual_v2" o "eleven_turbo_v2".
DEFAULT_MODEL: str = os.getenv("ENTITA_MODEL", "eleven_v3")

# Formato compatibile con Starter; se vedi 403 prova "mp3_44100_64" o "mp3_44100_32".
OUT_FMT: str = os.getenv("ENTITA_FORMAT", "mp3_44100_64")

# ---------------------------------------------------------------------------

if not API_KEY:
    sys.exit("API key mancante. Imposta ELEVEN_API_KEY o XI_API_KEY nell'ambiente.")

_client = ElevenLabs(api_key=API_KEY)


def read_text_from_argv() -> str:
    """Per test da CLI: prende testo da argomenti o da file .txt, altrimenti input()."""
    if len(sys.argv) > 1 and not sys.argv[1].endswith(".txt"):
        return " ".join(sys.argv[1:])
    if len(sys.argv) > 1 and sys.argv[1].endswith(".txt"):
        return pathlib.Path(sys.argv[1]).read_text(encoding="utf-8")
    return input("Testo da pronunciare: ")


def _convert_stream(text: str, voice_id: str, model_id: str, output_format: str):
    """
    Chiama l'API TTS e restituisce lo stream (iterabile di chunk).
    Include un piccolo fallback automatico se il piano non consente il formato richiesto.
    """
    try:
        return _client.text_to_speech.convert(
            text=text,
            voice_id=voice_id,
            model_id=model_id,
            output_format=output_format,
            # niente voice_settings: usa il profilo della voce che hai creato
        )
    except ApiError as e:
        # Fallback su formati più permissivi se il piano non consente il richiesto
        if getattr(e, "status_code", None) in (401, 402, 403):
            for fmt in ("mp3_44100_64", "mp3_44100_32"):
                if fmt == output_format:
                    continue
                try:
                    return _client.text_to_speech.convert(
                        text=text, voice_id=voice_id, model_id=model_id, output_format=fmt
                    )
                except ApiError:
                    continue
        raise


def speak(text: str, *, voice_id: Optional[str] = None, model_id: Optional[str] = None,
          output_format: Optional[str] = None) -> None:
    """
    Riproduce subito l'audio con la tua voce ENTITÀ (via ffplay/winsound).
    """
    v_id = voice_id or VOICE_ID
    m_id = model_id or DEFAULT_MODEL
    fmt  = output_format or OUT_FMT

    audio = _convert_stream(text, v_id, m_id, fmt)
    play(audio)


def tts_to_file(text: str, out_path: str, *, voice_id: Optional[str] = None,
                model_id: Optional[str] = None, output_format: Optional[str] = None) -> str:
    """
    Genera audio con la tua voce ENTITÀ e lo salva in 'out_path'.
    Ritorna il percorso assoluto del file salvato.
    """
    v_id = voice_id or VOICE_ID
    m_id = model_id or DEFAULT_MODEL
    fmt  = output_format or OUT_FMT

    stream = _convert_stream(text, v_id, m_id, fmt)
    p = pathlib.Path(out_path)
    p.parent.mkdir(parents=True, exist_ok=True)

    with open(p, "wb") as f:
        for chunk in stream:
            if chunk:
                f.write(chunk)
    return str(p.resolve())


def ensure_cached_tts(text: str, out_path: str, **kwargs) -> str:
    """
    Se 'out_path' esiste lo riusa; altrimenti genera e salva.
    Ritorna il percorso assoluto.
    """
    p = pathlib.Path(out_path)
    if p.exists():
        return str(p.resolve())
    return tts_to_file(text, out_path, **kwargs)


# ----------------------------------------------------------------------------
# CLI per test veloci: `python -m engine.engine_eleven_labs "Testo..."`.
# ----------------------------------------------------------------------------
if __name__ == "__main__":
    speak(read_text_from_argv())
    print("Fatto.")
# ----------------------------------------------------------------------------
