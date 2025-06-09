import logging
import yaml
import requests
import json

# Load config.yaml
try:
    with open("config.yaml") as f:
        CONFIG = yaml.safe_load(f)
except Exception as e:
    logging.error("Failed to load config.yaml: %s", e)
    CONFIG = {}

def generate_gpt_message(bio_text):
    if not CONFIG.get("gpt", {}).get("enabled", False):
        logging.warning("GPT/Ollama is disabled in config. Skipping generation.")
        return None

    logging.info('Generating message using Ollama...')

    prompt = (
        f"You are a {CONFIG['gpt']['personality']} person trying to message someone on Hinge.\n"
        f"Their bio is:\n\"{bio_text}\"\n"
        f"Write a {CONFIG['gpt']['style']} opener that sounds natural, not generic."
    )

    try:
        res = requests.post(
            "http://localhost:11434/api/generate",
            json={"model": CONFIG['gpt'].get("model", "mistral"), "prompt": prompt},
            stream=True
        )
        res.raise_for_status()
        message = ""
        for line in res.iter_lines():
            if line:
                data = json.loads(line)
                if "response" in data:
                    message += data["response"]
        message = message.strip()
        logging.info("Generated message: %s", message)
        return message

    except Exception as e:
        logging.error("Ollama API Error: %s", e)
        return None
