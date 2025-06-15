import logging
import numpy as np
import cv2
import time
import hashlib
import os
from PIL import Image
import pytesseract
from utils.humanizer import wait_random
import xml.etree.ElementTree as ET
from utils.gpt_generator import is_message_suitable


logging.basicConfig(level=logging.INFO, format='[%(asctime)s] %(levelname)s: %(message)s')

# Replace with your emulator window title (e.g., "BlueStacks", "Nox", "Android Emulator", etc.)


def find_and_interact_with_buttons(message=None):
    """
    Analyzes screenshots while scrolling to find buttons and interact with them.
    Only clicks the like button if the message is suitable for the prompt text found near the button.
    Optimized for OnePlus 10 emulated device (1080x2400 resolution).
    
    Args:
        screenshot_path: Path to the initial screenshot
        target_prompt_text: The prompt text we want to reply to (optional)
        message: The message to send (used to decide if button is suitable)
    
    Returns:
        tuple: (success, button_coords) where success is bool and button_coords is (x,y) or None
    """
    logging.info('Starting button search with scrolling...')
    
    # OnePlus 10 specific parameters
    SCREEN_WIDTH = 1080
    SCREEN_HEIGHT = 2400
    SCROLL_START_Y = 2000  # Start scroll from near bottom
    SCROLL_END_Y = 1000    # End scroll near top
    SCROLL_DURATION = 300  # ms
    SCROLL_DELAY = 1.5     # seconds between scrolls
    
    # Load the reply button template image
    template_path = "LikeImagePromt.png"
    if not os.path.exists(template_path):
        logging.error(f"Reply button template image not found at {template_path}")
        return False, None
        
    template = cv2.imread(template_path)
    if template is None:
        logging.error("Failed to load reply button template")
        return False, None
        
    # Convert template to grayscale
    template_gray = cv2.cvtColor(template, cv2.COLOR_BGR2GRAY)
    template_h, template_w = template_gray.shape
    
    # Scroll and search parameters
    max_scrolls = 6  # Increased for taller screen
    scroll_count = 0
    last_screenshot_hash = None
    same_screenshot_count = 0
    max_same_screenshots = 3  # Stop if we see the same content 3 times
    
    def get_screenshot_hash(image_path):
        """Get hash of image to detect duplicate screenshots"""
        try:
            with open(image_path, 'rb') as f:
                return hashlib.md5(f.read()).hexdigest()
        except Exception as e:
            logging.error(f"Error hashing image {image_path}: {e}")
            return None
    
    def scroll_screen():
        """Scroll the screen with OnePlus 10 specific parameters"""
        os.system(f'adb shell input swipe 500 1500 500 800 300')
        time.sleep(SCROLL_DELAY)
    
    def take_screenshot(filename):
        """Take a screenshot using ADB"""
        os.system(f"adb exec-out screencap -p > {filename}")
        time.sleep(0.5)  # Wait for screenshot to be saved

    
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
    
    
    
    def find_best_match(screenshot_gray, template_gray):
        """Find the best match using multiple template matching methods"""
        methods = [
            cv2.TM_CCOEFF_NORMED,
            cv2.TM_CCORR_NORMED,
            cv2.TM_SQDIFF_NORMED
        ]
        
        best_confidence = 0
        best_location = None
        
        for method in methods:
            result = cv2.matchTemplate(screenshot_gray, template_gray, method)
            min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)
            
            # For TM_SQDIFF_NORMED, the best match is the minimum value
            if method == cv2.TM_SQDIFF_NORMED:
                confidence = 1 - min_val  # Convert to similarity score
                location = min_loc
            else:
                confidence = max_val
                location = max_loc
                
            if confidence > best_confidence:
                best_confidence = confidence
                best_location = location
                
        return best_confidence, best_location
    
    def get_button_coordinates_from_ui_dump(xml_path, button_class="android.widget.Button", content_desc=None):
        """
        Extracts coordinates of all clickable buttons from the UI dump XML.
        Optionally filter by class or content-desc.
        """
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
    
    def find_prompt_above_button(xml_path, button_x, button_y):
        tree = ET.parse(xml_path)
        root = tree.getroot()
        best_prompt = None
        best_dist = float('inf')
        for node in root.iter("node"):
            text = node.attrib.get("text", "") or node.attrib.get("content-desc", "")
            if text.strip() and len(text.strip()) > 3:  # Ignore very short/generic text
                bounds = node.attrib["bounds"]
                left_top, right_bottom = bounds.split("][")
                left, top = map(int, left_top[1:].split(","))
                right, bottom = map(int, right_bottom[:-1].split(","))
                # Only consider prompts above the button
                if bottom < button_y:
                    dist = button_y - bottom
                    if dist < best_dist and dist < 300:  # Only if not too far away
                        best_dist = dist
                        best_prompt = (left, top, right, bottom, text)
        return best_prompt  # (left, top, right, bottom, text) or None
    
    while scroll_count < max_scrolls:
        logging.info(f"Scroll attempt {scroll_count + 1}/{max_scrolls}")
        try:
            # Take a new screenshot after each scroll
            if scroll_count > 0:
                scroll_screen()
            current_screenshot = f'scroll_check_{scroll_count}.png'
            take_screenshot(current_screenshot)
            # Dump and pull UI XML
            os.system('adb shell uiautomator dump /sdcard/ui.xml')
            os.system('adb pull /sdcard/ui.xml ui_dump.xml')
            # Get button coordinates from UI dump
            button_coords = get_button_coordinates_from_ui_dump('ui_dump.xml',  button_class="android.widget.Button", content_desc="Like")
            screenshot = Image.open(current_screenshot)
            screenshot_np = np.array(screenshot)
            found = False
            for (x, y, left, top, right, bottom) in button_coords:
                # Crop around the button for OCR and image check
                crop_margin = 100
                crop_left = max(left - crop_margin, 0)
                crop_top = max(top - crop_margin, 0)
                crop_right = min(right + crop_margin, screenshot_np.shape[1])
                crop_bottom = min(bottom + crop_margin, screenshot_np.shape[0])
                region = screenshot_np[crop_top:crop_bottom, crop_left:crop_right]
                region_pil = Image.fromarray(region)
                prompt_info = find_prompt_above_button('ui_dump.xml', x, y)
                if prompt_info:
                    left, top, right, bottom, prompt_text = prompt_info
                    region = screenshot_np[top:bottom, left:right]
                    region_pil = Image.fromarray(region)
                    ocr_text = pytesseract.image_to_string(region_pil)
                    logging.info(f"Prompt text near button: {prompt_text.strip()}")
                    # (Optional) Image check: template match in this region
                    region_gray = cv2.cvtColor(np.array(region_pil), cv2.COLOR_RGB2GRAY)
                    confidence, location = find_best_match(region_gray, template_gray)
                    if confidence > 0.45:
                        logging.info(f"Image check passed for button at ({x}, {y}) with confidence {confidence:.2f}")
                        # LLM check
                        if message and prompt_text:
                            logging.info("Asking Ollama if this is a good reply...")
                            if is_message_suitable(prompt_text, message):
                                logging.info("Ollama says this is a good reply. Clicking button.")
                                if click_button(x, y):
                                    logging.info("Successfully clicked button")
                                    try:
                                        os.remove(current_screenshot)
                                    except:
                                        pass
                                    found = True
                                    return True, (x, y)
                                else:
                                    logging.warning("Failed to click button, trying again...")
                                    time.sleep(0.5)
                                    if click_button(x, y):
                                        logging.info("Successfully clicked button on second attempt")
                                        try:
                                            os.remove(current_screenshot)
                                        except:
                                            pass
                                        found = True
                                        return True, (x, y)
                            else:
                                logging.info("Ollama says this is NOT a good reply. Skipping this button.")
                    else:
                        logging.info(f"Image check failed for button at ({x}, {y}) (confidence: {confidence:.2f})")
                else:
                    logging.info(f"No prompt found above button at ({x}, {y})")
            if not found:
                try:
                    os.remove(current_screenshot)
                except:
                    pass
                logging.info(f"No suitable button found in current view.")
                scroll_count += 1
        except Exception as e:
            logging.error(f"Error during scroll attempt {scroll_count + 1}: {e}")
            try:
                os.remove(current_screenshot)
            except:
                pass
            scroll_count += 1
    logging.warning(f"Could not find suitable reply button after {scroll_count} scrolls")
    return False, None


# if __name__ == "__main__":
#     while True:
#         find_and_interact_with_buttons("You look like you will ruin my life in a sexy way")
#         wait_random(15, 30)
