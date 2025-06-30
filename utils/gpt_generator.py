import logging
import yaml
import requests
import json


# my lines
curated_lines = []



# Load config.yaml
try:
    with open("config.yaml") as f:
        CONFIG = yaml.safe_load(f)
except Exception as e:
    logging.error("Failed to load config.yaml: %s", e)
    CONFIG = {}

def generate_gpt_message(bio_text):
    examples = "\n".join(f"- {line}" for line in curated_lines)
    if not CONFIG.get("gpt", {}).get("enabled", False):
        logging.warning("GPT/Ollama is disabled in config. Skipping generation.")
        return None

    logging.info('Generating message using Ollama...')


    prompt = f"""
    You're a {CONFIG['gpt']['personality']} person trying to send a fun and flirty first message on Hinge.

    Their bio: "{bio_text}"
    They are {CONFIG['gpt']['target_age']} and looking for a {CONFIG['gpt']['target_relationship']} relationship.

    If their name is mentioned, feel free to make a funny or clever pun using it — as long as it's light, playful, and not forced.

    Write a clever and specific opener that:
    - Feels confident, human, and personal
    - Is flirty, playful, and optionally a little sarcastic
    - Uses only letters, numbers, and spaces
    - Is under 100 characters

    Here are some examples of the tone to aim for, you can also create similar lines
    {examples}

    ❗ Important:
    - Do NOT include lines like “we'd be that couple,” “soulmate,” “romantic journey,” or “decode each other's signs”
    - Avoid anything dreamy, overly deep, or sentimental
    - Avoid emojis, quotes, lists, or explanations
    - Allowed characters: A-Z, a-z, and SPACE only.
    - Only return the final message line to send
    - Avoid generic flattery (e.g., “you look amazing”)
    - Do not reference age, religion, or city
    - Do not include hashtags or greetings like “Hi” or “Hello”
    - Do not use dramatic phrasing like “emotional damage,” “ruin me,” “soulmate,” or “hot mess energy”
    - Avoid vague romantic clichés. Keep it fresh and specific.
    - Do NOT copy any example exactly unless it perfectly matches the prompt.
    - do not make plane
    - no lines regarding spirit animals, zodiac signs, or astrology
    - Do NOT suggest plans or shared activities, just a fun opener
    - donot start with "If we matched," or similar phrases that imply a match is already made

    Before returing the final Recheck the message and see if it is good and follow above instruction

    Return only the final message. 
    """

    # prompt = f"""
    # You’re a {CONFIG['gpt']['personality']} person crafting a fun, flirty Hinge opener.
    # Their bio: "{bio_text}"
    # Write a clever, playful message:
    # - Confident, personal, and a bit sarcastic
    # - Under 100 characters
    # - Only letters, numbers, and spaces
    # Examples: {examples}
    # Return only the final message.
    # """

    # prompt = f"""
    # You’re crafting a flirty Hinge opener. Their bio: "Loves night vibes and spontaneous adventures."
    # Write a clever, playful message under 100 characters using only letters, numbers, and spaces.
    # Absolutely NO emojis, punctuation, or special characters.
    # Their bio: "{bio_text}"
    # Absolutely NO emojis, punctuation, or special characters.
    # Do NOT suggest plans or shared activities.
    # Return only the final message.
    # """

    # prompt = f"""
    # You’re a witty, flirty person crafting a Hinge opener.
    # Their bio: "{bio_text}"
    # Write a playful message under 100 characters using ONLY letters, numbers, and spaces.
    # NO emojis, punctuation, or special characters. NO plans or shared activities.
    # Examples: {examples}
    # Return only the final message.
    # """

    try:
        res = requests.post(
            "http://localhost:11434/api/generate",
            json={"model": CONFIG['gpt'].get("model", "llama3.1:8b-instruct-q4_0"), "prompt": prompt, "temperature": 0.1,  
            "max_tokens": 30 },
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


def is_message_suitable(prompt_text, message, model="llama3.1:8b-instruct-q4_0"):
    """Ask Ollama if the message is a good reply to the prompt text."""
    system_prompt = (
        f'Prompt: "{prompt_text.strip()}"\n'
        f'Message: "{message.strip()}"\n'
        'Is this message a good, relevant, and contextually appropriate reply to the prompt? Reply with only "yes" or "no".'
    )
    try:
        res = requests.post(
            "http://localhost:11434/api/generate",
            json={"model": model, "prompt": system_prompt},
            timeout=10
        )
        res.raise_for_status()
        response = res.text.strip().lower()
        return "yes" in response
    except Exception as e:
        logging.error(f"Ollama API error: {e}")
        return False