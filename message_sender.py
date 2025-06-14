import subprocess
import time
import logging
import re

def send_message(x, y, message):
    try:
        # No need to tap again since button is already clicked
        logging.info('Preparing to send message...')
        time.sleep(1)  # Wait for input field to be ready

        # Remove unsupported characters (like emojis)
        safe_message = re.sub(r'[^\x00-\x7F]', '', message)  # Keep only ASCII characters
        # Remove problematic shell characters for adb shell input text
        safe_message = re.sub(r'[\'\"\\\\`$&|;<>]', '', safe_message)
        # Remove newlines and carriage returns
        safe_message = safe_message.replace('\n', ' ').replace('\r', ' ')
        # Collapse multiple spaces
        safe_message = re.sub(r'\s+', ' ', safe_message).strip()

        if not safe_message:
            logging.error("Message is empty after sanitization")
            return False

        logging.info(f'Sending message in chunks: {safe_message}')
        max_length = 100  # ADB input text limit (conservative)
        for i in range(0, len(safe_message), max_length):
            chunk = safe_message[i:i+max_length]
            # Escape special characters for ADB shell
            chunk = chunk.replace(' ', '\\ ').replace('&', '\\&').replace(';', '\\;')
            subprocess.run(["adb", "shell", "input", "text", f'"{chunk}"'], check=True)
            time.sleep(0.2)

        logging.info('Tapping send button (keyevent 66)...')
        subprocess.run(["adb", "shell", "input", "keyevent", "66"], check=True)  # Keyevent 66 = Enter
        return True

    except subprocess.CalledProcessError as e:
        logging.error(f"ADB command failed: {e}")
        return False
    except Exception as e:
        logging.error(f"Error sending message: {e}")
        return False
