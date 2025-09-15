# engine/entity_brain.py
# -*- coding: utf-8 -*-

import re
import random
from typing import Optional

import torch
from transformers import GPT2LMHeadModel, GPT2Tokenizer


class EntityBrain:
    """
    Generatore di risposte per l'ENTITÀ basato su GPT-2.
    Migliorie principali:
      - pad_token_id impostato (usa eos come pad)
      - attention_mask sempre passato al model.generate()
      - uso di max_new_tokens (al posto di max_length)
      - gestione device (cuda/cpu) e modalità inference
      - filtri lessicali + memoria anti-ripetizione
      - probabilità di rispondere configurabile (respond_prob)
    """

    def __init__(
        self,
        model_path: str,
        device: Optional[str] = None,
        respond_prob: float = 0.5,        
    ):
        self.device = device or ("cuda" if torch.cuda.is_available() else "cpu")

        # Tokenizer
        self.tokenizer = GPT2Tokenizer.from_pretrained(model_path)
        # GPT-2 non ha pad di default -> usa EOS come pad
        if self.tokenizer.pad_token_id is None:
            self.tokenizer.pad_token_id = self.tokenizer.eos_token_id
        # (opzionale) padding a destra, tipico per causal LM
        self.tokenizer.padding_side = "right"

        # Modello
        self.model = GPT2LMHeadModel.from_pretrained(model_path)
        self.model.to(self.device)
        # Allinea config di generazione
        self.model.config.pad_token_id = self.tokenizer.pad_token_id
        if self.model.config.eos_token_id is None and self.tokenizer.eos_token_id is not None:
            self.model.config.eos_token_id = self.tokenizer.eos_token_id

        # Stato conversazionale semplice
        self.last_responses = []
        self.respond_prob = respond_prob

    # --------------------------
    # Filtri di validità (tuoi)
    # --------------------------
    def is_valid_response(self, text: str) -> bool:
        """
        Controlla se il testo è valido:
        - Non deve essere solo punteggiatura o parole senza senso
        - Deve contenere almeno una parola significativa
        """
        if not text or text.strip() in [".", "...", "-", "–", "—"]:
            return False

        cleaned = text.strip().lower()
        if len(cleaned) < 5:
            return False

        # Esclude solo consonanti o vocali ripetute senza senso
        if re.fullmatch(r"[bcdfghjklmnpqrstvwxyz]{3,}", cleaned):
            return False
        if re.fullmatch(r"[aeiou]{3,}", cleaned):
            return False

        # Esclude parole inventate molto strane (es: sequenze con molte x, q, z)
        if re.search(r"[xqz]{3,}", cleaned):
            return False

        return True

    # --------------------------
    # Generazione
    # --------------------------
    @torch.inference_mode()
    def generate_response(
        self,
        prompt: str,
        max_new_tokens: int = 60,
        temperature: float = 1.2,
        top_k: int = 40,
        top_p: float = 0.92,
        repetition_penalty: float = 1.15,
    ) -> Optional[str]:
        """
        Genera una breve risposta dell'ENTITÀ a partire dall'ultima riga del prompt.
        Ritorna None se decide di non rispondere o se il testo generato non supera i filtri.
        """

        # Gate probabilistico (come il tuo: risponde solo a volte)
        if random.random() > self.respond_prob:
            return None

        # Prendi solo l'ultima riga come contesto diretto
        last_line = prompt.strip().split("\n")[-1] if "\n" in prompt else prompt.strip()
        cleaned_prompt = f"{last_line}\nENTITÀ:"

        # Tokenizzazione + attention_mask (fondamentale per evitare il warning)
        enc = self.tokenizer(
            cleaned_prompt,
            return_tensors="pt",
            padding=True,       # in caso di batch futuro, già pronto
            truncation=True,
        )
        input_ids = enc["input_ids"].to(self.device)
        attention_mask = enc["attention_mask"].to(self.device)

        # Generazione: usa max_new_tokens (non max_length)
        out = self.model.generate(
            input_ids=input_ids,
            attention_mask=attention_mask,
            max_new_tokens=max_new_tokens,
            do_sample=True,
            temperature=temperature,
            top_k=top_k,
            top_p=top_p,
            repetition_penalty=repetition_penalty,
            pad_token_id=self.tokenizer.pad_token_id,
            eos_token_id=self.tokenizer.eos_token_id,
        )

        # Solo la continuazione generata
        gen_ids = out[0, input_ids.shape[1]:]
        text = self.tokenizer.decode(gen_ids, skip_special_tokens=True)
        generated = text.strip()

        # Pulisci prefissi/punteggiatura iniziale ridondante
        generated = generated.lstrip(".:;-– ").strip()

        # Prendi max 2 frasi "pulite"
        sentences = re.split(r"[.!?]", generated)
        valid_sentences = [s.strip() for s in sentences if self.is_valid_response(s)]
        if not valid_sentences:
            return None

        final = ". ".join(valid_sentences[:2]).strip()
        if final and not final.endswith("."):
            final += "."

        # Capitalizza la prima lettera
        if final:
            final = final[0].upper() + final[1:]

        # Evita ripetizioni recenti
        if final in self.last_responses:
            return None

        self.last_responses.append(final)
        if len(self.last_responses) > 10:
            self.last_responses.pop(0)

        return final
