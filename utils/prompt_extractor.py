import os
import xml.etree.ElementTree as ET


def load_known_prompts(prompts_file):
    """
    Loads known Hinge prompts from a text file into a set for fast lookup.
    """
    prompts = set()
    with open(prompts_file, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if line:
                prompts.add(line)
    return prompts


def extract_prompt_response_pairs_from_xml(xml_path, known_prompts):
    """
    Parses a Hinge UI dump XML file and extracts prompt-response pairs.
    Args:
        xml_path (str): Path to the UI dump XML file.
        known_prompts (set): Set of known prompt strings.
    Returns:
        List of (prompt, response) tuples.
    """
    tree = ET.parse(xml_path)
    root = tree.getroot()
    nodes = list(root.iter('node'))
    pairs = []
    i = 0
    while i < len(nodes):
        node = nodes[i]
        text = node.attrib.get('text', '').strip()
        if text in known_prompts:
            # Try to find the next non-empty text node as the response
            response = None
            for j in range(i+1, min(i+4, len(nodes))):
                rtext = nodes[j].attrib.get('text', '').strip()
                if rtext and rtext not in known_prompts:
                    response = rtext
                    break
            pairs.append((text, response))
            i = j  # Skip to after the response
        else:
            i += 1
    return pairs


def extract_prompts_from_multiple_xml(xml_dir, prompts_file):
    """
    Extracts all prompt-response pairs from all XML files in a directory.
    Args:
        xml_dir (str): Directory containing UI dump XML files.
        prompts_file (str): Path to known prompts text file.
    Returns:
        Dict mapping XML filename to list of (prompt, response) tuples.
    """
    known_prompts = load_known_prompts(prompts_file)
    result = {}
    for fname in os.listdir(xml_dir):
        if fname.endswith('.xml'):
            xml_path = os.path.join(xml_dir, fname)
            pairs = extract_prompt_response_pairs_from_xml(xml_path, known_prompts)
            result[fname] = pairs
    return result
