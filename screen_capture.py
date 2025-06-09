import os
import time
import logging

def capture_screen(output_path='screen.png'):
    logging.info('Capturing screen using adb...')
    os.system("adb exec-out screencap -p > screen.png")
    time.sleep(1)
    logging.info(f'Screen saved to {output_path}')
    return "screen.png"
