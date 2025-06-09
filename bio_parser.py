import pytesseract
from PIL import Image, UnidentifiedImageError
import re
import yaml
import logging

def extract_text_from_image(image_path):
    try:
        logging.info(f'Opening image: {image_path}')
        image = Image.open(image_path)
        text = pytesseract.image_to_string(image)
        logging.info('Text extracted from image successfully.')
        return text
    except UnidentifiedImageError:
        logging.error(f"Error: The file '{image_path}' is not a valid image.")
        return None

def load_rules():
    with open('config.yaml') as f:
        return yaml.safe_load(f)['rules']

def match_rules(text, rules):
    logging.info('Matching rules...')
    for rule in rules:
        condition = rule['condition']
        if "contains" in condition:
            keyword = condition.split("contains")[1].strip()
            if keyword.lower() in text.lower():
                logging.info(f"Rule matched: contains '{keyword}'")
                return rule['message']
        elif "startswith" in condition:
            name_start = condition.split("startswith")[1].strip()
            name = extract_name(text)
            if name and name.lower().startswith(name_start.lower()):
                logging.info(f"Rule matched: startswith '{name_start}'")
                return rule['message']
    logging.info('No rules matched.')
    return None

def extract_name(text):
    match = re.search(r'Name:\s*(\w+)', text)
    return match.group(1) if match else None
