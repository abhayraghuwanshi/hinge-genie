from utils.find_and_tap_button import find_and_tap_skip_button
from utils.find_button_coordinate_v1 import find_and_interact_with_buttons
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

from utils.smart_message_v1 import SmartMessageGenerator


curated_lines = [
    "If we match, I call dibs on being the little spoon at least twice a week.",
    "You seem like trouble… I like it",
    "What's your go-to red flag? I need to know what I'm ignoring.",
    "I'd offer a cheesy pickup line, but honestly, your pics are distracting me",
    "Would it be too forward to ask you what we're doing on our third date?",
    "What kind of trouble are we starting this week?",
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
    "You seem like the kind of person I'd make bad decisions with… and still blame astrology.",
    "If we matched in a new city, I'd say it was fate. If we matched here, I'd say it's time to book flights.",
    "You give off “takes spontaneous trips and makes questionable choices at the airport bar” energy. I respect it.",
    "Are you the algorithm? Because you're showing me things I didn't know I needed.",
    "You look like you'd understand my meme references and still judge me. Ideal"
]

with open("config.yaml") as f:
    CONFIG = yaml.safe_load(f)

rules = CONFIG.get("rules", [])
myMessageGenerator = SmartMessageGenerator(config_path="config.yaml", curated_lines=curated_lines)
logging.basicConfig(level=logging.INFO, format='[%(asctime)s] %(levelname)s: %(message)s')

def run_bot():
    logging.info('Creating a new session for the bot...................................................................')
    screen_to_top()
    # scroll and capture the screen into a single image
    screenshot_list = capture_full_page_screenshots(
        output_prefix='full_page',
        max_scrolls=7,
        scroll_delay=1.0
    )

    print("Screenshots captured:")
    for screenshot in screenshot_list:
        print(f"- {screenshot}")

    stitched_file = stitch_screenshots(screenshot_list, 'complete_page.png')
    if not stitched_file:
        logging.error("Failed to stitch screenshots. Cleaning up and skipping this iteration.")
        # Clean up temporary files
        for screenshot in screenshot_list:
            try:
                os.remove(screenshot)
            except:
                pass
        return

    # now extract all the prompt data from this -> using ocr
    logging.info('Extracting bio text from image...')
    ocr_text = extract_text_from_image(stitched_file)
    # logging.info(f'Extracted bio text: {cleaned_bio_text}')
    message = None

    # now we have all the data, generate prompt from the text extract
    if CONFIG["gpt"]["enabled"]:
        logging.info('Generating message using GPT...')
        message = myMessageGenerator.generate(ocr_text)
        logging.info(f'GPT message: {message}')

    messageSent = False
    if message:
        logging.info(f"[REQ FOUND] Sending message \n: {message}")
        screen_to_top()
        # First find and click the reply button, passing the bio text to match
        success, button_coords = find_and_interact_with_buttons(message)
        if success and button_coords:
            # Wait for input field to be ready
            wait_random(0.5, 1)
            # Send the message
            messageSent= send_message(message=message)
            # Save profile and message to history
            save_profile_and_message(stitched_file, message)
        else:
            
            logging.warning("Could not find matching reply button. Skipping message send.")
    else:
        logging.info('No suitable message found. Skipping.')
    if not messageSent:
        find_and_tap_skip_button()
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
        wait_duration = wait_random(10, 15)
        logging.info(f"--- Cycle complete. Waiting for {wait_duration} seconds. ---")