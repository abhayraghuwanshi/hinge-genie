import logging
import numpy as np
import cv2
import time
import hashlib
import os
from PIL import Image
import pyautogui  # Add this import for mouse control
import pygetwindow as gw
import pytesseract
import requests
from humanizer import wait_random
logging.basicConfig(level=logging.INFO, format='[%(asctime)s] %(levelname)s: %(message)s')

# Replace with your emulator window title (e.g., "BlueStacks", "Nox", "Android Emulator", etc.)
window_title = "BlueStacks App Player"  # Change this to match your emulator's window title

# Find the window
win = None
for w in gw.getAllWindows():
    if window_title.lower() in w.title.lower():
        win = w
        break

if win is None:
    raise Exception("Emulator window not found!")

offset_x, offset_y = 685, 41

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
    max_scrolls = 15  # Increased for taller screen
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
    
    
    def is_message_suitable(prompt_text, message, model="mistral"):
        """Ask Ollama if the message is a good reply to the prompt text."""
        system_prompt = (
            f'Prompt: "{prompt_text.strip()}"\n'
            f'Message: "{message.strip()}"\n'
            'Is this message a good, relevant, and contextually appropriate reply to the prompt? Reply with only "yes" or "no".'
        )
        try:
            res = requests.post(
                "http://localhost:11434/api/generate",
                json={"model": model, "prompt": system_prompt},
                timeout=10
            )
            res.raise_for_status()
            response = res.text.strip().lower()
            return "yes" in response
        except Exception as e:
            logging.error(f"Ollama API error: {e}")
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
    
    
    while scroll_count < max_scrolls:
        logging.info(f"Scroll attempt {scroll_count + 1}/{max_scrolls}")
        
        try:
            # Take a new screenshot after each scroll
            if scroll_count > 0:
                scroll_screen()
            
            current_screenshot = f'scroll_check_{scroll_count}.png'
            take_screenshot(current_screenshot)

            logging.info(Image.open("screen.png").size)  # Should return (1080, 2400)

            # Check if we've reached the end of content
            current_hash = get_screenshot_hash(current_screenshot)
            if current_hash == last_screenshot_hash:
                same_screenshot_count += 1
                logging.info(f"Same content detected ({same_screenshot_count}/{max_same_screenshots})")
                if same_screenshot_count >= max_same_screenshots:
                    logging.info("Reached end of content")
                    break
            else:
                same_screenshot_count = 0
                last_screenshot_hash = current_hash
            
            # Load and process the screenshot
            screenshot = Image.open(current_screenshot)
            screenshot_np = np.array(screenshot)
            screenshot_gray = cv2.cvtColor(screenshot_np, cv2.COLOR_RGB2GRAY)
            
            # Find best match using multiple methods
            confidence, location = find_best_match(screenshot_gray, template_gray)
            
            # Lower threshold since we're using multiple matching methods
            if confidence > 0.45:  # Adjusted threshold based on observed values
                # Get the center of the matched template
                x = location[0] + template_w//2
                y = location[1] + template_h//2
                
                logging.info(f"Found reply button at ({x}, {y}) with confidence {confidence:.2f}")
                
                # Extract text near the button
                crop_margin = 100  # pixels around the button
                left = max(location[0] - crop_margin, 0)
                top = max(location[1] - crop_margin, 0)
                right = min(location[0] + template_w + crop_margin, screenshot_np.shape[1])
                bottom = min(location[1] + template_h + crop_margin, screenshot_np.shape[0])
                region = screenshot_np[top:bottom, left:right]
                region_pil = Image.fromarray(region)
                prompt_text = pytesseract.image_to_string(region_pil)
                logging.info(f"Prompt text near button: {prompt_text.strip()}")
                
                # Decide if this is the right button based on the message and prompt text
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
                                return True, (x, y)
                    else:
                        logging.info("Ollama says this is NOT a good reply. Scrolling...")
            
            # Clean up temporary screenshot
            try:
                os.remove(current_screenshot)
            except:
                pass
            
            logging.info(f"No suitable button found in current view (confidence: {confidence:.2f})")
            scroll_count += 1
            
        except Exception as e:
            logging.error(f"Error during scroll attempt {scroll_count + 1}: {e}")
            # Clean up temporary screenshot
            try:
                os.remove(current_screenshot)
            except:
                pass
            scroll_count += 1
    
    logging.warning(f"Could not find suitable reply button after {scroll_count} scrolls")
    return False, None


if __name__ == "__main__":
    while True:
        find_and_interact_with_buttons("Hey there! I couldn't help but notice your love for Bob's place – we must have similar taste in comfort food and cozy spots! When I'm looking to unwind and feel a bit more like myself, it's usually the first place on my list too. Maybe we can plan a double date with our friends sometime? 🍔😉 Let's see if Bob's can work its magic on us both.")
        wait_random(15, 30)
