import os
import logging
import shutil
from datetime import datetime

# --- Directory and File Configuration ---
HISTORY_DIR = "history"
DUMPS_DIR = os.path.join(HISTORY_DIR, "dumps")
MATCHES_DIR = os.path.join(HISTORY_DIR, "new_matches")
PROFILES_DIR = os.path.join(HISTORY_DIR, "profiles")
MESSAGES_DIR = os.path.join(HISTORY_DIR, "messages")
INTERACTION_LOG_FILE = os.path.join(HISTORY_DIR, "interactions.log")

def setup_history_folders():
    """Creates the necessary history directories if they don't exist."""
    os.makedirs(DUMPS_DIR, exist_ok=True)
    os.makedirs(MATCHES_DIR, exist_ok=True)
    os.makedirs(PROFILES_DIR, exist_ok=True)
    os.makedirs(MESSAGES_DIR, exist_ok=True)
    logging.info("History folders are set up.")

def log_interaction(profile_name):
    """Logs that an interaction with a profile was completed."""
    with open(INTERACTION_LOG_FILE, "a") as f:
        f.write(f"{profile_name}\n")
    logging.info(f"Logged successful interaction with '{profile_name}'.")

def has_interacted(profile_name):
    """Checks if we have already interacted with this profile."""
    if not os.path.exists(INTERACTION_LOG_FILE):
        return False
    with open(INTERACTION_LOG_FILE, "r") as f:
        interacted_profiles = {line.strip().lower() for line in f}
    return profile_name.lower() in interacted_profiles

def save_dump_to_history(dump_file_path):
    """Saves a copy of the UI dump to the history/dumps folder with a timestamp."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    history_dump_path = os.path.join(DUMPS_DIR, f"dump_{timestamp}.xml")
    try:
        shutil.copy(dump_file_path, history_dump_path)
        logging.info(f"Saved UI dump to {history_dump_path}")
        return history_dump_path
    except IOError as e:
        logging.error(f"Failed to copy dump to history: {e}")
        return None

def save_new_match_dump(profile_name, dump_file_path):
    """Saves the UI dump for a new match to a special folder for review and returns the file path."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    match_dump_path = os.path.join(MATCHES_DIR, f"{profile_name}_{timestamp}.xml")
    try:
        shutil.copy(dump_file_path, match_dump_path)
        logging.info(f"Saved new match UI dump to {match_dump_path}")
        return match_dump_path
    except IOError as e:
        logging.error(f"Failed to save new match dump: {e}")
        return None

def save_profile_and_message(profile_image_path, message):
    """Saves the profile image and sent message to history with timestamp."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Save profile image
    profile_history_path = os.path.join(PROFILES_DIR, f"profile_{timestamp}.png")
    try:
        shutil.copy(profile_image_path, profile_history_path)
        logging.info(f"Saved profile image to {profile_history_path}")
    except IOError as e:
        logging.error(f"Failed to save profile image: {e}")
    
    # Save message
    message_history_path = os.path.join(MESSAGES_DIR, f"message_{timestamp}.txt")
    try:
        with open(message_history_path, "w", encoding="utf-8") as f:
            f.write(message)
        logging.info(f"Saved message to {message_history_path}")
    except IOError as e:
        logging.error(f"Failed to save message: {e}")

def save_prompt_and_response(prompt, response):
    """Saves the prompt and the generated response to history/prompt-response with timestamp."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    directory = "history/prompt-response"
    os.makedirs(directory, exist_ok=True)
    file_path = os.path.join(directory, f"prompt_response_{timestamp}.txt")
    try:
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(f"Prompt:\n{prompt}\n\nResponse:\n{response}\n")
        logging.info(f"Saved prompt and response to {file_path}")
    except IOError as e:
        logging.error(f"Failed to save prompt and response: {e}")