import subprocess
import time
import logging
import re

def send_message(x, y, message):
    logging.info(f'Tapping input field at ({x}, {y})...')
    subprocess.run(["adb", "shell", "input", "tap", str(x), str(y)])
    time.sleep(1)

    # Remove unsupported characters (like emojis)
    safe_message = re.sub(r'[^\w\s.,!?@#\$%\^&\*\(\)\-_=+\[\]{};:\'\"|<>,./\\]', '', message)
    # Remove problematic shell characters for adb shell input text
    safe_message = re.sub(r'[\'\"\\\\`$&|;<>]', '', safe_message)
    # Remove newlines and carriage returns
    safe_message = safe_message.replace('\n', ' ').replace('\r', ' ')
    # Collapse multiple spaces
    safe_message = re.sub(r'\\s+', ' ', safe_message)

    logging.info(f'Sending message in chunks: {safe_message}')
    max_length = 100  # ADB input text limit (conservative)
    for i in range(0, len(safe_message), max_length):
        chunk = safe_message[i:i+max_length].strip()
        chunk = chunk.replace(' ', '%s')
        subprocess.run(["adb", "shell", "input", "text", chunk])
        time.sleep(0.2)

    logging.info('Tapping send button (keyevent 66)...')
    subprocess.run(["adb", "shell", "input", "keyevent", "66"])  # Keyevent 66 = Enter
