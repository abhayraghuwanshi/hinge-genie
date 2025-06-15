import logging
import yaml
import requests
import json


# my lines
curated_lines = [
    "I don't do ‘plans,' BoJack. I do vibes.",
    "If we match, I call dibs on being the little spoon at least twice a week.",
    "You seem like trouble… I like it",
    "What's your go-to red flag? I need to know what I'm ignoring.",
    "I'd offer a cheesy pickup line, but honestly, your pics are distracting me",
    "Would it be too forward to ask you what we're doing on our third date?",
    "What kind of trouble are we starting this week?",
    "You look like you'd ruin my life in the best way possible. Shall we begin?",
    "I'd offer a cheesy pickup line, but honestly, your shoes are distracting me",
    "You look like you'd ghost me… but like, really politely.",
    "If we were both fries, you'd be the one I save for last. Just sayin'",
    "What's your spirit animal and why is it probably a raccoon in a leather jacket?",
    "You look like you give amazing advice and terrible life choices. Prove me right or disappoint me.",
    "You seem like the type who's either amazing at parallel parking or absolutely terrible. No in-between. Which is it?",
    "If we dated, I feel like you'd win 80% of our fake arguments. I'm okay with that.",
    "You seem like someone who'd casually ruin me emotionally… but in a hot way.",
    "What's your villain origin story? You definitely have one.",
    "Real question: do you look this cool or are you actually this cool?",
    "You'd be the hot girl in a heist movie who double-crosses everyone. I respect it",
    "Are you into guys who open with clever texts or the ones who make you question your life choices? I can do either",
    "I feel like dating you comes with terms and conditions. And I don't read fine print.",
    "You're probably a walking green flag with a red flag hobby. I'm intrigued.",
    "Are you the reason for my trust issues? Or the cure? Let's find out.",
    "You give off “I'll ruin your routine in the best way” energy.",
    "I feel like we'd be that couple people either ship hard or fear deeply. No middle ground.",
    "If emotional damage was a love language, I think we'd be fluent.",
    "You seem like the kind of person I'd make bad decisions with… and still blame astrology.",
    "If we matched in a new city, I'd say it was fate. If we matched here, I'd say it's time to book flights.",
    "You give off “takes spontaneous trips and makes questionable choices at the airport bar” energy. I respect it.",
    "Are you the algorithm? Because you're showing me things I didn't know I needed.",
    "You look like you'd understand my meme references and still judge me. Ideal"
]



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


    prompt = (
        "You are a {CONFIG['gpt']['personality']} person messaging someone on Hinge.\n"
        "Their bio is: \"{bio_text}\"\n"
        "Based on their interests and personality, write a {CONFIG['gpt']['style']} opening message that is natural, specific, and engaging, using only letters, numbers, and spaces, no emojis or special characters, and exactly 100 characters or fewer.\n"
        "Consider they are {CONFIG['gpt']['target_age']} years old and seeking a {CONFIG['gpt']['target_relationship']} relationship."
        f"Here are some example openers:\n{examples}\n\n"
        f"Pick the best line from the list above, OR write a new one in the same style.\n"
        f"Only respond with the final message to send."
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


def is_message_suitable(prompt_text, message, model="mistral"):
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