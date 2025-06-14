from find_button_corrdinates import find_all_prompts_and_likes_with_scrolling
from screen_capture import capture_full_page_screenshots, stitch_screenshots
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

    # scrooll and capture the screen into a single image
    screenshot_list = capture_full_page_screenshots(
        output_prefix='full_page',
        max_scrolls=7,
        scroll_delay=2.0
    )

    print("Screenshots captured:")
    for screenshot in screenshot_list:
        print(f"- {screenshot}")

    stitched_file = stitch_screenshots(screenshot_list, 'complete_page.png')

    # now extract all the promt data from this -> using ocr
    logging.info('Extracting bio text from image...')
    bio_text = extract_text_from_image(stitched_file)
    logging.info(f'Extracted bio text: {bio_text}')
    message = None

    # clean bio text from the model

    # now we have all the data, generate promt from the the text extract
    message = None

    if CONFIG["gpt"]["enabled"]:
        logging.info('Generating message using GPT...')
        message = generate_gpt_message(bio_text)
        logging.info(f'GPT message: {message}')

    # Finalise thebest promt to answer from the list of promts
    if not message:
        logging.info('Trying to match rules...')
        message = match_rules(bio_text, rules)
        logging.info(f'Rule-based message: {message}')

    # Autoscroll and find that promt:
    # how ? take screenshot find if there is a button to reply (images of button matching).
    # find the promt that in screen. 
    # find the coordinate of the reply button and if the reply promt is making sense
    # type the message in the input field 
    # find the cooridnate of the send button by taking screenshot and analysing the button coordinate
    if message:
        logging.info(f"[REQ FOUND] Sending message: {message}")
        wait_random(2, 4)
        send_message(x=320, y=890, message=message)


    # Do the house keeping of the images



  
    else:
        logging.info('No suitable message found. Skipping.')

if __name__ == "__main__":
    while True:
        run_bot()
        wait_random(15, 30)
