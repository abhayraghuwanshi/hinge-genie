from utils.find_button_corrdinates import find_and_interact_with_buttons
from utils.screen_capture import capture_full_page_screenshots, screen_to_top, stitch_screenshots
from utils.bio_parser import extract_text_from_image, match_rules, load_rules
from utils.message_sender import send_message
from utils.humanizer import wait_random
from utils.gpt_generator import generate_gpt_message
from utils.interaction_manager import setup_history_folders, save_profile_and_message
import logging
import os
import xml.etree.ElementTree as ElementTree
from PIL import Image
import numpy as np
import yaml

with open("config.yaml") as f:
    CONFIG = yaml.safe_load(f)

rules = CONFIG.get("rules", [])

logging.basicConfig(level=logging.INFO, format='[%(asctime)s] %(levelname)s: %(message)s')

def run_bot():
    logging.info('Creating a new session for the bot...................................................................')
    screen_to_top()
    # scroll and capture the screen into a single image
    screenshot_list = capture_full_page_screenshots(
        output_prefix='full_page',
        max_scrolls=7,
        scroll_delay=2.0
    )

    print("Screenshots captured:")
    for screenshot in screenshot_list:
        print(f"- {screenshot}")

    stitched_file = stitch_screenshots(screenshot_list, 'complete_page.png')

    # now extract all the prompt data from this -> using ocr
    logging.info('Extracting bio text from image...')
    bio_text = extract_text_from_image(stitched_file)
    logging.info(f'Extracted bio text: {bio_text}')
    message = None

    # now we have all the data, generate prompt from the text extract
    if CONFIG["gpt"]["enabled"]:
        logging.info('Generating message using GPT...')
        message = generate_gpt_message(bio_text)
        logging.info(f'GPT message: {message}')

    # Finalize the best prompt to answer from the list of prompts
    if not message:
        logging.info('Trying to match rules...')
        message = match_rules(bio_text, rules)
        logging.info(f'Rule-based message: {message}')

    if message:
        logging.info(f"[REQ FOUND] Sending message: {message}")
        wait_random(2, 4)
        screen_to_top()
        # First find and click the reply button, passing the bio text to match
        success, button_coords = find_and_interact_with_buttons(message)
        if success and button_coords:
            # Wait for input field to be ready
            wait_random(1, 2)
            # Send the message
            send_message(message=message)
            # Save profile and message to history
            save_profile_and_message(stitched_file, message)
        else:
            logging.warning("Could not find matching reply button. Skipping message send.")
    else:
        logging.info('No suitable message found. Skipping.')

    # Clean up temporary files
    for screenshot in screenshot_list:
        try:
            os.remove(screenshot)
        except:
            pass
    # Keep the stitched file for reference
    logging.info(f"Kept stitched profile image: {stitched_file}")

if __name__ == "__main__":
    # Ensure all necessary folders exist before starting the loop
    setup_history_folders()
    
    logging.info("Bot starting up. Press Ctrl+C to stop.")
    while True:
        run_bot()
        wait_duration = wait_random(60, 90)
        logging.info(f"--- Cycle complete. Waiting for {wait_duration} seconds. ---")