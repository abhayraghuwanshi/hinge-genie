import os
import time
import logging
import xml.etree.ElementTree as ET

def find_and_interact_with_buttons(message=None):
    logging.info('Finding and clicking the first reply button on screen...')

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
            screenshot_file = 'single_scroll.png'
            take_screenshot(screenshot_file)
            time.sleep(1)
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
