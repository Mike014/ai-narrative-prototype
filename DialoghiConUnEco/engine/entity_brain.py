from transformers import GPT2LMHeadModel, GPT2Tokenizer
import torch
import random
import re

class EntityBrain:
    def __init__(self, model_path):
        self.tokenizer = GPT2Tokenizer.from_pretrained(model_path)
        self.model = GPT2LMHeadModel.from_pretrained(model_path)
        self.last_responses = []

    def is_valid_response(self, text):
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

    def generate_response(self, prompt, max_length=200):
        if random.random() > 0.5:  # Risponde solo a volte
            return None

        last_line = prompt.strip().split("\n")[-1] if "\n" in prompt else prompt.strip()
        cleaned_prompt = f"{last_line}\nENTITÀ:"

        inputs = self.tokenizer.encode(cleaned_prompt, return_tensors="pt")
        outputs = self.model.generate(
            inputs,
            max_length=max_length,
            pad_token_id=self.tokenizer.eos_token_id,
            do_sample=True,
            top_k=40,
            top_p=0.92,
            temperature=1.2,
            repetition_penalty=1.15,
            num_return_sequences=1
        )

        text = self.tokenizer.decode(outputs[0], skip_special_tokens=True)
        generated = text[len(cleaned_prompt):].strip()

        # Pulisce punteggiatura iniziale
        generated = generated.lstrip(".:;-– ").strip()

        # Prende max 2 frasi
        sentences = re.split(r"[.!?]", generated)
        valid_sentences = [s.strip() for s in sentences if self.is_valid_response(s)]
        if not valid_sentences:
            return None

        generated = ". ".join(valid_sentences[:2]).strip() + "."

        # Capitalizza la prima lettera
        if generated:
            generated = generated[0].upper() + generated[1:]

        # Evita ripetizioni
        if generated in self.last_responses:
            return None

        self.last_responses.append(generated)
        if len(self.last_responses) > 10:
            self.last_responses.pop(0)

        return generated
