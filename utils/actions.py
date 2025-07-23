import os
import time
import logging
import xml.etree.ElementTree as ET
import hashlib
import numpy as np
import cv2
from PIL import Image
import pytesseract
import xml.etree.ElementTree as ET
import re
import subprocess
import time
from xml.etree import ElementTree
import logging
import os
import random
from utils.interaction_manager import save_dump_to_history


# Configuration
DUMP_FILE = "ui.xml"    
# Setup basic loggingaa
logging.basicConfig(level=logging.INFO, format='[%(asctime)s] %(levelname)s: %(message)s')


def find_and_interact_with_like_buttons(message=None):
    logging.info('Finding and clicking the first like button on screen...')

    def take_screenshot(filename):
        os.system(f"adb exec-out screencap -p > {filename}")
        time.sleep(0.5)

    def scroll_screen_once():
        os.system(f'adb shell input swipe 500 1500 500 800 300')
        time.sleep(1.2)

    def get_button_coordinates_from_ui_dump(xml_path, button_class="android.widget.Button", content_desc="Like"):
        tree = ET.parse(xml_path)
        root = tree.getroot()
        coords = []
        for node in root.iter("node"):
            if node.attrib.get("clickable") == "true":
                if button_class and node.attrib.get("class") != button_class:
                    continue
                if content_desc and content_desc not in node.attrib.get("content-desc", ""):
                    continue
                bounds = node.attrib["bounds"]
                left_top, right_bottom = bounds.split("][")
                left, top = map(int, left_top[1:].split(","))
                right, bottom = map(int, right_bottom[:-1].split(","))
                x = (left + right) // 2
                y = (top + bottom) // 2
                coords.append((x, y))
        return coords

    def click_button(x, y):
        result = os.system(f"adb shell input tap {int(x)} {int(y)}")
        if result == 0:
            logging.info(f"✅ Tapped at ({x}, {y})")
            return True
        else:
            logging.error("❌ ADB tap command failed")
            return False

    try:
        # Scroll once before capturing
        for _ in range(2):
            # Dump UI hierarchy
            os.system('adb shell uiautomator dump /sdcard/ui.xml')
            os.system('adb pull /sdcard/ui.xml ui_dump.xml')

            # Find first like button
            button_coords = get_button_coordinates_from_ui_dump('ui_dump.xml')
            if button_coords:
                x, y = button_coords[0]
                logging.info(f"Found first button at ({x}, {y})")
                if click_button(x, y):
                    return True, (x, y)
            scroll_screen_once()

        logging.warning("No reply button found.")
        return False, None

    except Exception as e:
        logging.error(f"Error in single-pass button finder: {e}")
        return False, None


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
        logging.error("Failed to parse UI dump XML.")



def take_screenshot(filename):
    """Take a screenshot using ADB and save to filename."""
    os.system(f"adb exec-out screencap -p > {filename}")
    time.sleep(0.5)

def scroll_screen(start_x=500, start_y=1500, end_x=500, end_y=800, duration=300, delay=1.2):
    """Scroll the screen by swiping from (start_x, start_y) to (end_x, end_y)."""
    os.system(f'adb shell input swipe {start_x} {start_y} {end_x} {end_y} {duration}')
    time.sleep(delay)

def take_ui_dump():
    """Dumps the current UI, saves it to history, and returns the local file path."""
    logging.info("[*] Taking UIAutomator dump...")
    adb_shell("uiautomator dump /sdcard/ui.xml")
    subprocess.run(["adb", "pull", "/sdcard/ui.xml", DUMP_FILE], capture_output=True)
    if os.path.exists(DUMP_FILE):
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

def get_button_coordinates_from_ui_dump(xml_path, button_class="android.widget.Button", content_desc=None):
    """Extracts coordinates of all clickable buttons from the UI dump XML. Optionally filter by class or content-desc."""
    tree = ET.parse(xml_path)
    root = tree.getroot()
    coords = []
    for node in root.iter("node"):
        if node.attrib.get("clickable") == "true":
            if button_class and node.attrib.get("class") != button_class:
                continue
            if content_desc and content_desc not in node.attrib.get("content-desc", ""):
                continue
            bounds = node.attrib["bounds"]
            left_top, right_bottom = bounds.split("][")
            left, top = map(int, left_top[1:].split(","))
            right, bottom = map(int, right_bottom[:-1].split(","))
            x = (left + right) // 2
            y = (top + bottom) // 2
            coords.append((x, y, left, top, right, bottom))
    return coords


def click_button(x, y):
    """Use ADB to tap at given screen coordinates."""
    try:
        adb_x = int(x)
        adb_y = int(y)
        result = os.system(f"adb shell input tap {adb_x} {adb_y}")
        if result == 0:
            logging.info(f"Tapped at ({adb_x}, {adb_y}) using ADB")
            return True
        else:
            logging.error("ADB tap command failed.")
            return False
    except Exception as e:
        logging.error(f"Error during adb tap: {e}")
        return False

def get_input_field_coordinates(xml_path):
    """Extracts coordinates of the input field from the UI dump XML."""
    tree = ET.parse(xml_path)
    root = tree.getroot()
    for node in root.iter("node"):
        if node.attrib.get("class") == "android.widget.EditText" and node.attrib.get("clickable") == "true":
            return parse_bounds(node.attrib["bounds"])
    return None, None

def get_send_button_coordinates(xml_path):
    """Extracts coordinates of the send button from the UI dump XML."""
    tree = ET.parse(xml_path)
    root = tree.getroot()
    for node in root.iter("node"):
        content_desc = node.attrib.get("content-desc", "").lower()
        if "send priority like" in content_desc:
            for parent in root.iter("node"):
                if node in list(parent):
                    if parent.attrib.get("clickable") == "true":
                        return parse_bounds(parent.attrib["bounds"])
    return None, None

def get_cancel_button_coordinates(xml_path):
    """Extracts coordinates of the cancel button from the UI dump XML."""
    tree = ET.parse(xml_path)
    root = tree.getroot()
    for node in root.iter("node"):
        # Check both content-desc and text attributes
        content_desc = node.attrib.get("content-desc", "").lower()
        text = node.attrib.get("text", "").lower()
        if content_desc == "cancel" or text == "cancel":
            # If we found a text node, get its parent button
            if node.attrib.get("class") == "android.widget.TextView":
                for parent in root.iter("node"):
                    if node in list(parent) and parent.attrib.get("class") == "android.widget.Button":
                        return parse_bounds(parent.attrib["bounds"])
            return parse_bounds(node.attrib["bounds"])
    return None, None


def find_and_tap_skip_button():
    """Finds and taps the button to skip the current profile."""
    logging.info("Attempting to find and tap the 'Skip' button.")
    dump_path = take_ui_dump()
    if not dump_path: return False

    try:
        tree = ET.parse(dump_path)
        root = tree.getroot()
        
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

    except ET.ParseError:
        logging.error("Failed to parse UI dump for skip button.")
    
    return False

def click_on_like_button_type_and_send_message(message):
    try:
        logging.info('Preparing to send message...')
        time.sleep(2)

        logging.info('Dumping UI hierarchy to find input field...')
        subprocess.run(['adb', 'shell', 'uiautomator', 'dump', '/sdcard/ui.xml'], check=True)
        subprocess.run(['adb', 'pull', '/sdcard/ui.xml', 'ui_dump.xml'], check=True)
        input_x, input_y = get_input_field_coordinates('ui_dump.xml')

        if input_x is not None and input_y is not None:
            logging.info(f'Found input field at ({input_x}, {input_y}). Tapping it...')
            subprocess.run(["adb", "shell", "input", "tap", str(input_x), str(input_y)], check=True)
            time.sleep(2.5)
        else:
            logging.error("Input field not found in UI dump.")
            return False

        safe_message = re.sub(r'[^\x00-\x7F]', '', message)
        safe_message = re.sub(r'[\'\"\\\\`$&|;<>]', '', safe_message)
        safe_message = safe_message.replace('\n', ' ').replace('\r', ' ')
        safe_message = re.sub(r'\s+', ' ', safe_message).strip()

        if not safe_message:
            logging.error("Message is empty after sanitization")
            return False

        logging.info(f'Clearing input field...')
        subprocess.run(["adb", "shell", "input", "keyevent", "67"], check=True)  # Clear the input field
        time.sleep(0.2)
        max_length = 100
        for i in range(0, len(safe_message), max_length):
            chunk = safe_message[i:i+max_length]
            chunk = chunk.replace(' ', '%s')
            subprocess.run(["adb", "shell", "input", "text", chunk], check=True)
            time.sleep(0.2)

        send_x, send_y = get_send_button_coordinates('ui_dump.xml')

        if send_x is not None and send_y is not None:
            logging.info(f'Tapping send button at ({send_x}, {send_y})...')
            time.sleep(1)
            subprocess.run(["adb", "shell", "input", "tap", str(send_x), str(send_y)], check=True)
            return True
        else:
            logging.error("Send button not found.")
            return False

    except subprocess.CalledProcessError as e:
        logging.error(f"ADB command failed: {e}")
        # Attempt to close the dialog by clicking the cancel button
        cancel_x, cancel_y = get_cancel_button_coordinates('ui_dump.xml')
        if cancel_x is not None and cancel_y is not None:
            logging.info(f'Attempting to close dialog by tapping cancel button at ({cancel_x}, {cancel_y})...')
            subprocess.run(["adb", "shell", "input", "tap", str(cancel_x), str(cancel_y)], check=True)
            return False
        else:
            logging.error("Cancel button not found.")
            return False
    except Exception as e:
        cancel_x, cancel_y = get_cancel_button_coordinates('ui_dump.xml')
        if cancel_x is not None and cancel_y is not None:
            logging.info(f'Attempting to close dialog by tapping cancel button at ({cancel_x}, {cancel_y})...')
            subprocess.run(["adb", "shell", "input", "tap", str(cancel_x), str(cancel_y)], check=True)
            return False
        else:
            logging.error("Cancel button not found.")
            return False

def scroll_to_top():
    logging.info('Scrolling to the top before starting full page screenshot capture...')
    # Scroll to the top by sending multiple swipe-up gestures
    for _ in range(8):
        # Swipe up: start_y < end_y (move from lower to upper part of the screen)
        os.system('adb shell input swipe 500 800 500 1500 300')
        time.sleep(0.5)
    logging.info('Reached top of the page.')

def scroll_and_save_ui_dumps(folder_path=None, scroll_count=6, delay=1.2):
    """
    Scrolls the screen `scroll_count` times, taking a UI dump after each scroll and saving
    each dump as an XML file in `folder_path` (default: 'history/tmp'). Dumps are named dump_1.xml, dump_2.xml, ...
    Args:
        folder_path (str): Directory to save UI dump XML files.
        scroll_count (int): Number of scrolls/UI dumps to perform.
        delay (float): Seconds to wait after each scroll before dumping UI.
    """
    if folder_path is None:
        folder_path = os.path.join('history', 'tmp')
    os.makedirs(folder_path, exist_ok=True)
    for i in range(scroll_count):
        # Dump UI
        dump_name = os.path.join(folder_path, f"dump_{i+1}.xml")
        os.system('adb shell uiautomator dump /sdcard/ui.xml')
        os.system(f'adb pull /sdcard/ui.xml "{dump_name}"')
        logging.info(f"Saved UI dump: {dump_name}")
        # Scroll screen
        os.system('adb shell input swipe 500 1500 500 800 300')
        time.sleep(delay)


def wait_random(min_seconds=2, max_seconds=5):
    time.sleep(random.uniform(min_seconds, max_seconds))



