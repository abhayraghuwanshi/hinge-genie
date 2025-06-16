import re
import subprocess
import time
from xml.etree import ElementTree
import logging
from utils.interaction_manager import save_dump_to_history
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

def extract_prompts_from_dump(dump_file=DUMP_FILE):
    """
    Extract exactly 3 prompt blocks:
    - Each block consists of 2 consecutive TextViews (prompt title + response)
    - Followed by a Like button with content-desc "like" or "heart"
    """
    try:
        tree = ElementTree.parse(dump_file)
    except (FileNotFoundError, ElementTree.ParseError):
        logging.error("Could not parse XML file.")
        return []

    root = tree.getroot()
    prompts = []
    temp_prompt = []
    seen_prompts = set()

    for node in root.iter("node"):
        clazz = node.attrib.get("class", "")
        text = node.attrib.get("text", "").strip()
        desc = node.attrib.get("content-desc", "").lower()

        if clazz == "android.widget.TextView" and text:
            temp_prompt.append(text)
            if len(temp_prompt) == 2:
                core_id = " | ".join(temp_prompt).lower()
                if core_id not in seen_prompts:
                    prompts.append({
                        "id": core_id,
                        "prompt_text": " | ".join(temp_prompt),
                        "like_coords": None
                    })
                    seen_prompts.add(core_id)
                temp_prompt = []

        elif "like" in desc or "heart" in desc:
            if clazz == "android.widget.Button" and prompts:
                bounds = node.attrib.get("bounds")
                coords = parse_bounds(bounds)
                if coords and prompts[-1]["like_coords"] is None:
                    prompts[-1]["like_coords"] = coords

        if len(prompts) == 3:
            break
    
    return prompts

    root = tree.getroot()
    extracted_data = []

    # Recursively walk the tree to find prompt blocks
    for parent in root.iter('node'):
        # Gather consecutive TextViews (prompt title and answer)
        prompt_texts = []
        like_button_node = None

        children = list(parent)
        i = 0
        while i < len(children):
            node = children[i]
            if node.attrib.get("class") == "android.widget.TextView":
                text = node.attrib.get("text", "").strip()
                if text:
                    prompt_texts.append(text)
                i += 1
                # Check for a second TextView (the answer)
                if i < len(children) and children[i].attrib.get("class") == "android.widget.TextView":
                    text2 = children[i].attrib.get("text", "").strip()
                    if text2:
                        prompt_texts.append(text2)
                    i += 1
                # After TextViews, check for a sibling android.view.View containing a Like button
                if i < len(children):
                    maybe_like_container = children[i]
                    if (maybe_like_container.attrib.get("class") == "android.view.View"):
                        # Look for a Button with content-desc="Like" inside
                        for subnode in maybe_like_container.iter('node'):
                            if (subnode.attrib.get("class") == "android.widget.Button" and
                                subnode.attrib.get("content-desc", "") == "Like"):
                                like_button_node = subnode
                                break
                        if like_button_node is not None:
                            i += 1  # Move past the like container
                # If we found both prompt text and a like button, record it
                if prompt_texts and like_button_node is not None:
                    full_prompt = " | ".join(prompt_texts)
                    like_bounds = like_button_node.attrib.get("bounds")
                    like_coords = parse_bounds(like_bounds)
                    if like_coords:
                        prompt_id = (full_prompt, like_bounds)
                        extracted_data.append({
                            "id": prompt_id,
                            "prompt_text": full_prompt,
                            "like_coords": like_coords
                        })
                # Reset for next possible prompt in this parent
                prompt_texts = []
                like_button_node = None
            else:
                i += 1

    return extracted_data


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

def find_all_prompts_and_likes_with_scrolling(max_swipes=30):
    """
    Scans the entire UI by scrolling, extracting all unique prompts and their 'Like' buttons.

    Args:
        max_swipes (int): A safeguard to prevent infinite scrolling.

    Returns:
        list: A list of dictionaries, each containing the 'prompt_text'
              and the 'like_coords' (a tuple of x, y).
    """
    logging.info("--- Starting full-page scan with scrolling ---")
    
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
        prompts_on_screen = extract_prompts_from_dump(DUMP_FILE)
        
        new_prompts_found = 0
        for prompt in prompts_on_screen:
            if prompt["id"] not in all_found_prompts:
                all_found_prompts[prompt["id"]] = prompt
                new_prompts_found += 1
        
        logging.info(f"[+] Found {new_prompts_found} new prompts on this screen.")

    return list(all_found_prompts.values())
