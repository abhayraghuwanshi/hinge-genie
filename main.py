from screen_capture import capture_screen
from bio_parser import extract_text_from_image, match_rules, load_rules
from message_sender import send_message
from humanizer import wait_random
from gpt_generator import generate_gpt_message
import yaml
import logging

with open("config.yaml") as f:
    CONFIG = yaml.safe_load(f)

rules = CONFIG.get("rules", [])

logging.basicConfig(level=logging.INFO, format='[%(asctime)s] %(levelname)s: %(message)s')

def run_bot():
    logging.info('Capturing screen...')
    image_path = capture_screen()
    logging.info(f'Screen captured: {image_path}')
    logging.info('Extracting bio text from image...')
    bio_text = extract_text_from_image(image_path)
    logging.info(f'Extracted bio text: {bio_text}')
    message = None

    if CONFIG["gpt"]["enabled"]:
        logging.info('Generating message using GPT...')
        message = generate_gpt_message(bio_text)
        logging.info(f'GPT message: {message}')

    if not message:
        logging.info('Trying to match rules...')
        message = match_rules(bio_text, rules)
        logging.info(f'Rule-based message: {message}')

    if message:
        logging.info(f"[MATCH FOUND] Sending message: {message}")
        wait_random(2, 4)
        send_message(x=320, y=890, message=message)
    else:
        logging.info('No suitable message found. Skipping.')

if __name__ == "__main__":
    while True:
        run_bot()
        wait_random(15, 30)
