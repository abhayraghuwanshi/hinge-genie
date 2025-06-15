
import subprocess
import time
import logging
import re
import xml.etree.ElementTree as ET
from humanizer import wait_random

def parse_bounds(bounds):
    left_top, right_bottom = bounds.split("][")
    left, top = map(int, left_top[1:].split(","))
    right, bottom = map(int, right_bottom[:-1].split(","))
    x = (left + right) // 2
    y = (top + bottom) // 2
    return x, y

def get_input_field_coordinates(xml_path):
    tree = ET.parse(xml_path)
    root = tree.getroot()
    for node in root.iter("node"):
        if node.attrib.get("class") == "android.widget.EditText" and node.attrib.get("clickable") == "true":
            return parse_bounds(node.attrib["bounds"])
    return None, None

def get_send_button_coordinates(xml_path):
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

def send_message(message):
    try:
        logging.info('Preparing to send message...')
        time.sleep(1)

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

        logging.info('Dumping UI to locate send button...')
        subprocess.run(['adb', 'shell', 'uiautomator', 'dump', '/sdcard/ui.xml'], check=True)
        subprocess.run(['adb', 'pull', '/sdcard/ui.xml', 'ui_dump.xml'], check=True)
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
        return False
    except Exception as e:
        logging.error(f"Error sending message: {e}")
        return False

# if __name__ == "__main__":
#     while True:
#         send_message("Hello you look like you will ruin my life in the best way possible")
#         wait_random(15, 30)
