import os
import logging
import shutil
from datetime import datetime

# --- Directory and File Configuration ---
HISTORY_DIR = "history"
DUMPS_DIR = os.path.join(HISTORY_DIR, "dumps")
MATCHES_DIR = os.path.join(HISTORY_DIR, "new_matches")
INTERACTION_LOG_FILE = os.path.join(HISTORY_DIR, "interactions.log")

def setup_history_folders():
    """Creates the necessary history directories if they don't exist."""
    os.makedirs(DUMPS_DIR, exist_ok=True)
    os.makedirs(MATCHES_DIR, exist_ok=True)
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