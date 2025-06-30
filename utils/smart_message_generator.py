import logging
import yaml
import requests
import json
import re

class SmartMessageGenerator:
    def __init__(self, config_path="config.yaml", curated_lines=None):
        try:
            with open(config_path) as f:
                self.CONFIG = yaml.safe_load(f)
        except Exception as e:
            logging.error("Failed to load config.yaml: %s", e)
            self.CONFIG = {}

        self.curated_lines = curated_lines or []
        self.max_retries = 3

    def _build_prompt(self, bio_text):
        examples = "\n".join(f"- {line}" for line in self.curated_lines)
        return f"""You're a {self.CONFIG['gpt']['personality']} person trying to send a fun and flirty first message on Hinge.
        Their bio: "{bio_text}"
        They are {self.CONFIG['gpt']['target_age']} and looking for a {self.CONFIG['gpt']['target_relationship']} relationship.

        If their name is mentioned, feel free to make a funny or clever pun using it — as long as it's light, playful, and not forced.

        Write a clever and specific opener that:
        - Feels confident, human, and personal
        - Is flirty, playful, and optionally a little sarcastic
        - Uses only letters, numbers, and spaces
        - Is under 100 characters
        - Do NOT suggest plans or shared activities, just a fun opener

        Here are some examples of the tone to aim for:
        {examples}

        ❗ Final instructions:
        - Return only one complete message line.
        - The message must be:
        - Less than 100 characters
        - A single sentence (no bullets, names, greetings, or sign-offs)
        - Without quotes, line breaks, punctuation, or emojis
        - Using only A-Z, a-z, 0-9 and SPACE
        - Do NOT suggest plans or shared activities, just a fun opener
        - donot start with "If we matched," or similar phrases that imply a match is already made
        - no lines regarding spirit animals, zodiac signs, or astrology
        - Do NOT suggest plans or shared activities, just a fun opener
        - donot start with "If we matched," or similar phrases that imply a match is already made
        - no wingman lines, no "let's meet" or similar phrases
        - no lines that imply a match is already made

        ✅ Double-check your response.
        If it breaks even one rule, rephrase and fix it before returning.
        Return only the message text. Nothing else.
        """

    def _is_valid_message(self, msg):
        msg = msg.strip()
        if len(msg) > 130:
            return False
        if not re.fullmatch(r"[A-Za-z0-9 ]+", msg):
            return False
        banned_patterns = [
            r"\n", r"[\"']+", r"\b[A-Z]\s?Man\b", r"5[\'′] ?\d+",
            r"\b[A-Z]{2,}\b", r"(listen to|before we meet|follow me|let's meet|let's grab|let's go|let's do|let's hang out|let's catch up|let's chat|let's talk|let's connect|let's vibe|let's explore|let's discover|let's experience|let's enjoy|let's have fun| wingman | astrology| shoe | cheesy pickup|If we matched | wingman | whirlpool | spontaneous)\b",
        ]
        return not any(re.search(pat, msg, re.IGNORECASE) for pat in banned_patterns)

    def _generate_raw_message(self, prompt):
        try:
            res = requests.post(
                "http://localhost:11434/api/generate",
                json={
                    "model": self.CONFIG['gpt'].get("model", "llama3.1:8b-instruct-q4_0"),
                    "prompt": prompt,
                    "temperature": 0.7,
                    "top_p": 0.9
                },
                stream=True
            )
            res.raise_for_status()
            message = ""
            for line in res.iter_lines():
                if line:
                    data = json.loads(line)
                    if "response" in data:
                        message += data["response"]
            return message.strip()
        except Exception as e:
            logging.error("Ollama API Error: %s", e)
            return None

    def generate(self, bio_text):
        prompt = self._build_prompt(bio_text)
        for attempt in range(self.max_retries):
            message = self._generate_raw_message(prompt)
            if message and self._is_valid_message(message):
                logging.info("✅ Valid message: %s", message)
                return message
            logging.warning("❌ Invalid message on attempt %d: %s", attempt + 1, message)
        return None
