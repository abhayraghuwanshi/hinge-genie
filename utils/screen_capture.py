import os
import logging
import time
from PIL import Image
import hashlib

logging.basicConfig(level=logging.INFO)

def capture_screen(output_path='screen.png'):
    """Capture a single screenshot"""
    logging.info(f'Capturing screen to {output_path}...')
    os.system(f"adb exec-out screencap -p > {output_path}")
    time.sleep(0.5)
    logging.info(f'Screen saved to {output_path}')
    return output_path

def scroll_down():
    """Scroll down on the device"""
    # Adjust coordinates based on your device resolution
    # Format: adb shell input swipe start_x start_y end_x end_y duration_ms
    os.system('adb shell input swipe 500 1500 500 800 300')
    logging.info('Scrolled down')

def get_image_hash(image_path):
    """Get hash of image to detect duplicate screenshots"""
    try:
        with open(image_path, 'rb') as f:
            return hashlib.md5(f.read()).hexdigest()
    except Exception as e:
        logging.error(f"Error hashing image {image_path}: {e}")
        return None

def capture_full_page_screenshots(output_prefix='page_screenshot', max_scrolls=7, scroll_delay=1.5):
    """
    Scrolls through the entire page and captures screenshots at each step.

    Args:
        output_prefix (str): Prefix for screenshot filenames
        max_scrolls (int): Maximum number of scrolls to prevent infinite loops
        scroll_delay (float): Delay between scroll and screenshot

    Returns:
        list: List of screenshot file paths
    """
    """
    Scrolls through the entire page and captures screenshots at each step.

    Args:
        output_prefix (str): Prefix for screenshot filenames
        max_scrolls (int): Maximum number of scrolls to prevent infinite loops
        scroll_delay (float): Delay between scroll and screenshot

    Returns:
        list: List of screenshot file paths
    """
    logging.info('Starting full page screenshot capture...')

    screenshot_files = []
    previous_screenshot_hash = None
    unchanged_count = 0
    max_unchanged = 3  # Stop after 3 identical screenshots

    for i in range(max_scrolls):
        # Capture current screen
        screenshot_path = f"{output_prefix}_{i:03d}.png"
        capture_screen(screenshot_path)
        screenshot_files.append(screenshot_path)

        # Check if screenshot is identical to previous one (reached end)
        current_hash = get_image_hash(screenshot_path)

        if current_hash == previous_screenshot_hash:
            unchanged_count += 1
            logging.info(f"Screenshot {i}: Identical to previous ({unchanged_count}/{max_unchanged})")

            if unchanged_count >= max_unchanged:
                logging.info("Reached end of page - stopping capture")
                break
        else:
            unchanged_count = 0
            logging.info(f"Screenshot {i}: New content captured")

        previous_screenshot_hash = current_hash

        # Scroll down for next screenshot
        if i < max_scrolls - 1:  # Don't scroll after last iteration
            scroll_down()
            time.sleep(scroll_delay)

    logging.info(f'Captured {len(screenshot_files)} screenshots')
    return screenshot_files

def stitch_screenshots(screenshot_files, output_path='stitched_image.png', overlap_pixels=0):
    """
    Stitch multiple screenshots into one long image

    Args:
        screenshot_files (list): List of screenshot file paths
        output_path (str): Output path for stitched image
        overlap_pixels (int): Number of pixels to overlap between images
    """
    try:
        if not screenshot_files:
            logging.error("No screenshots to stitch")
            return None

        # Verify all files exist
        for file in screenshot_files:
            if not os.path.exists(file):
                logging.error(f"Screenshot file not found: {file}")
                return None

        # Open first image to get dimensions
        first_img = Image.open(screenshot_files[0])
        img_width, img_height = first_img.size
        logging.info(f"First image dimensions: {img_width}x{img_height}")

        # Calculate total height (subtract overlap for each join)
        total_height = img_height + (img_height - overlap_pixels) * (len(screenshot_files) - 1)
        logging.info(f"Creating stitched image with dimensions: {img_width}x{total_height}")

        # Create new image
        stitched_img = Image.new('RGB', (img_width, total_height))

        # Paste images
        y_offset = 0
        for i, screenshot_file in enumerate(screenshot_files):
            logging.info(f"Processing screenshot {i+1}/{len(screenshot_files)}: {screenshot_file}")
            img = Image.open(screenshot_file)
            stitched_img.paste(img, (0, y_offset))
            if i < len(screenshot_files) - 1:  # Don't add overlap after last image
                y_offset += img_height - overlap_pixels

        stitched_img.save(output_path)
        logging.info(f'Stitched image saved to {output_path}')
        return output_path

    except ImportError:
        logging.error("PIL (Pillow) not installed. Install with: pip install Pillow")
        return None
    except Exception as e:
        logging.error(f"Error stitching images: {str(e)}")
        return None

def screen_to_top():
    logging.info('Scrolling to the top before starting full page screenshot capture...')
    # Scroll to the top by sending multiple swipe-up gestures
    for _ in range(8):
        # Swipe up: start_y < end_y (move from lower to upper part of the screen)
        os.system('adb shell input swipe 500 800 500 1500 300')
        time.sleep(0.5)
    logging.info('Reached top of the page.')