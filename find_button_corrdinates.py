import re
import subprocess
import time
from xml.etree import ElementTree
import logging
from interaction_manager import save_dump_to_history
import os
# Configuration
DUMP_FILE = "ui.xml"
# Setup basic loggingaa
logging.basicConfig(level=logging.INFO, format='[%(asctime)s] %(levelname)s: %(message)s')

def adb_shell(cmd):
    """Executes an adb shell command and returns the output."""
    try:
        return subprocess.run(["adb", "shell"] + cmd.split(), capture_output=True, text=True, check=True).stdout.strip()
    except subprocess.CalledProcessError as e:
        logging.error(f"ADB command failed: {e.stderr}")
        return None

def take_ui_dump():
    """Dumps the current UI, saves it to history, and returns the local file path."""
    logging.info("[*] Taking UIAutomator dump...")
    adb_shell("uiautomator dump /sdcard/ui.xml")
    subprocess.run(["adb", "pull", "/sdcard/ui.xml", DUMP_FILE], capture_output=True)
    
    if os.path.exists(DUMP_FILE):
        # Save a copy to the history/dumps folder
        save_dump_to_history(DUMP_FILE)
        return DUMP_FILE
    else:
        logging.error("UI dump file not found after pull.")
        return None

def parse_bounds(bounds_str):
    """Parses a bounds string like '[x1,y1][x2,y2]' into center (x, y) coordinates."""
    match = re.match(r"\[(\d+),(\d+)\]\[(\d+),(\d+)\]", bounds_str)
    if match:
        x1, y1, x2, y2 = map(int, match.groups())
        return (x1 + x2) // 2, (y1 + y2) // 2
    return None, None

def tap_screen(x, y):
    """Taps the screen at the given coordinates."""
    logging.info(f"[+] Tapping at ({x}, {y})...")
    adb_shell(f"input tap {x} {y}")

def find_and_tap_skip_button():
    """Finds and taps the button to skip the current profile."""
    logging.info("Attempting to find and tap the 'Skip' button.")
    dump_path = take_ui_dump()
    if not dump_path: return False

    try:
        tree = ElementTree.parse(dump_path)
        root = tree.getroot()
        
        # --- MODIFIED PART ---
        # Manually iterate to find the correct node instead of using complex XPath
        skip_node = None
        for node in root.iter('node'):
            if (node.attrib.get('class') == 'android.widget.Button' and
                    node.attrib.get('content-desc', '').startswith('Skip')):
                skip_node = node
                break  # Found the node, no need to search further
        # --- END OF MODIFIED PART ---

        if skip_node is not None:
            logging.info(f"Found skip button with description: '{skip_node.attrib.get('content-desc')}'")
            bounds = skip_node.attrib.get("bounds")
            x, y = parse_bounds(bounds)
            if x is not None and y is not None:
                tap_screen(x, y)
                logging.info("Successfully tapped the 'Skip' button.")
                return True
            else:
                logging.error("Found skip button but could not parse its bounds.")
        else:
            logging.warning("Could not find the 'Skip' button on the screen.")

    except ElementTree.ParseError:
        logging.error("Failed to parse UI dump for skip button.")
    
    return False

def extract_profile_name(dump_file=DUMP_FILE):
    """Extracts the profile's name from the UI dump."""
    try:
        tree = ElementTree.parse(dump_file)
        root = tree.getroot()
        # From the UI dump, the user's name is in a TextView that is uniquely focused
        name_node = root.find(".//*[@focusable='true'][@focused='true']")
        if name_node is not None and name_node.attrib.get("text"):
            name = name_node.attrib.get("text", "").strip()
            if name:
                logging.info(f"Extracted profile name: '{name}'")
                return name
    except (FileNotFoundError, ElementTree.ParseError):
        logging.error(f"Could not read or parse dump file: {dump_file}")

    logging.warning("Could not extract profile name.")
    return None

def get_clickable_button_coordinates(dump_file=DUMP_FILE):
    """
    Extracts the coordinates of all clickable buttons from the UI dump.

    Args:
        dump_file (str): Path to the UI XML dump file.

    Returns:
        list of dict: Each dict contains 'class', 'content-desc', 'text', and 'coords' (tuple of x, y).
    """
    try:
        tree = ElementTree.parse(dump_file)
    except (FileNotFoundError, ElementTree.ParseError):
        logging.error("Could not parse XML file.")
        return []

    root = tree.getroot()
    buttons = []

    for node in root.iter("node"):
        clazz = node.attrib.get("class", "")
        clickable = node.attrib.get("clickable", "false")
        if clazz == "android.widget.Button" and clickable == "true":
            bounds = node.attrib.get("bounds")
            coords = parse_bounds(bounds)
            button_info = {
                "class": clazz,
                "content-desc": node.attrib.get("content-desc", ""),
                "text": node.attrib.get("text", ""),
                "coords": coords
            }
            buttons.append(button_info)

    return buttons


def swipe_screen(x1=540, y1=1600, x2=540, y2=400, duration_ms=500):
    """
    Performs a swipe gesture to scroll the screen down.

    Default values (x1=540, y1=1600, x2=540, y2=400) are set for a typical 1080x1920 screen,
    which is common for Android emulators like Bluestacks. If your Bluestacks instance uses
    a different resolution, you may need to adjust these values accordingly.

    Args:
        x1, y1: Start coordinates of the swipe.
        x2, y2: End coordinates of the swipe.
        duration_ms: Duration of the swipe in milliseconds.
    """
    logging.info(f"[*] Swiping screen from ({x1}, {y1}) to ({x2}, {y2}) over {duration_ms}ms...")
    cmd = f"input swipe {x1} {y1} {x2} {y2} {duration_ms}"
    adb_shell(cmd)
    time.sleep(2)  # Wait for the UI to settle after swipe

    
# --- Main Functions (keep find_all_prompts_and_likes_with_scrolling as is) ---

def find_all_prompts_and_likes_with_scrolling(max_swipes=8):
    """
    Scans the entire UI by scrolling, extracting all unique prompts and their 'Like' buttons.

    Args:
        max_swipes (int): A safeguard to prevent infinite scrolling.

    Returns:
        list: A list of dictionaries, each containing the 'prompt_text'
              and the 'like_coords' (a tuple of x, y).
    """
    logging.info("--- Starting full-page scan with scrolling ---")

    logging.info('Scrolling to the top before starting full page screenshot capture...')
    # Scroll to the top by sending multiple swipe-up gestures
    for _ in range(8):
        # Swipe up: start_y < end_y (move from lower to upper part of the screen)
        os.system('adb shell input swipe 500 800 500 1500 300')
        time.sleep(0.5)
    logging.info('Reached top of the page.')
    
    all_found_prompts = {}
    last_content = ""
    same_content_count = 0
    max_same_content = 2  # If we see the same content 2 times in a row, assume we're done

    for i in range(max_swipes):
        logging.info(f"--- Scan Iteration {i+1}/{max_swipes} ---")
        
        current_content = take_ui_dump()

        if not current_content:
            logging.info("[✓] No UI dump content. Stopping scan.")
            break

        # If the UI content hasn't changed, try swiping a few more times before giving up.
        if current_content == last_content:
            same_content_count += 1
            logging.info(f"[!] UI content unchanged ({same_content_count}/{max_same_content}).")
            if same_content_count < max_same_content:
                logging.info("[*] UI unchanged, will try swiping again to ensure we've reached the end.")
                swipe_screen()
                continue
            else:
                # Instead of breaking immediately, try a few more swipes to ensure we reach the true end
                logging.info("[*] UI unchanged after several checks, but will attempt a few more swipes to ensure end.")
                for extra_swipe in range(3):
                    swipe_screen()
                    time.sleep(1)
                    current_content = take_ui_dump()
                    if current_content != last_content:
                        same_content_count = 0
                        break
                else:
                    logging.info("[✓] Reached the end of the page or UI is static after extra swipes.")
                    break
        else:
            same_content_count = 0

        last_content = current_content
        prompts_on_screen = get_clickable_button_coordinates(DUMP_FILE)
        
        
        logging.info(f"[+] Found {prompts_on_screen} new prompts on this screen.")

    return list(all_found_prompts.values())
