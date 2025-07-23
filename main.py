import logging
import os
import yaml
from utils.actions import find_and_interact_with_like_buttons, find_and_tap_skip_button, \
    click_on_like_button_type_and_send_message, scroll_to_top, wait_random, scroll_and_save_ui_dumps

from utils.interaction_manager import setup_history_folders, save_prompt_and_response
from utils.llm import llm  

logging.basicConfig(level=logging.INFO, format='[%(asctime)s] %(levelname)s: %(message)s')


def run_bot():
    logging.info('Creating a new session for the bot...................................................................')
    scroll_to_top()

    # now extract all the prompt data from this -> using ocr
    message = None
    scroll_and_save_ui_dumps()
    from utils.prompt_extractor import extract_prompts_from_multiple_xml
    result = extract_prompts_from_multiple_xml("history/tmp", "history/allPromts.txt")
    logging.info(result)
    scroll_to_top()

    # result is a dict: {filename: [(prompt, answer), ...], ...}
    pairs = []
    for file_results in result.values():
        for prompt, answer in file_results:
            pairs.append(f"{prompt}: {answer}")

    prompts = "\n".join(pairs)
    logging.info(prompts)

    gpt_prompt = (
        "You are an expert at writing witty and charming responses for Hinge, but your main goal is to sound authentic and easy to talk to. "
        "Given the following prompts from a user's profile, generate a single, engaging reply that increases the chances of a match. "
        
        # NEW INSTRUCTION FOR SIMPLICITY
        "Use simple, common English words and a conversational tone, as if you were texting a friend. Avoid complex vocabulary or formal phrasing. "
        
        "Your tone should be inquisitive and playful. "
        "Do not generalize specific details like decades or niche interests. "
        "Crucially, your response must end with an open-ended question to make it easy to reply. "
        "Be concise and avoid clichés. Do not use any emojis. Your response must be a maximum of 140 characters.\n\n"
        f"Profile Prompts:\n{prompts}\n\n"
        "Your Response (max 140 chars, simple English, must end with a question, no emoji):"
    )

    try:
        message = llm.call(gpt_prompt)
    except Exception as e:
        logging.error(f"Failed to generate response: {str(e)}")
        message = None

    if message:
        logging.info("\n" + "*" * 60)
        logging.info(f"GENERATED MESSAGE: {message}")
        logging.info("*" * 60 + "\n")

    messageSent = False
    if message:
        logging.info(f"[REQ FOUND] Sending message \n: {message}")
        # First find and click the reply button, passing the bio text to match
        success, button_coords = find_and_interact_with_like_buttons(message)
        if success and button_coords:
            logging.info(f"Found reply button at {button_coords}. Clicking and sending message...")
            wait_random(0.5, 1)
            # Send the message
            messageSent = click_on_like_button_type_and_send_message(message=message)
            # Save profile and message to history
            save_prompt_and_response(prompts, message)
        else:
            logging.warning("Could not find matching reply button. Skipping message send.")
    else:
        logging.info('No suitable message found. Skipping.')

    if not messageSent:
        find_and_tap_skip_button()
  

if __name__ == "__main__":
    # Ensure all necessary folders exist before starting the loop
    setup_history_folders()

    logging.info("Bot starting up. Press Ctrl+C to stop.")
    while True:
        run_bot()
        wait_duration = wait_random(10, 15)
        logging.info(f"--- Cycle complete. Waiting for {wait_duration} seconds. ---")