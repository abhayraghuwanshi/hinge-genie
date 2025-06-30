import logging
import yaml
import requests
import json
import re
import re
import logging
from difflib import SequenceMatcher

# --- Configuration ---
# It's good practice to configure logging at the start of your script.
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class SmartMessageGenerator:
    """
    Generates clever, personalized, and flirty opening messages for dating apps
    by analyzing a user's bio.
    """
    def __init__(self, config_path="config.yaml", curated_lines=None):
        """
        Initializes the generator with configuration and example lines.

        Args:
            config_path (str): Path to the YAML configuration file.
            curated_lines (list, optional): A list of high-quality example messages
                                            to guide the model's tone. Defaults to None.
        """
        try:
            with open(config_path) as f:
                self.CONFIG = yaml.safe_load(f)
        except FileNotFoundError:
            logging.error(f"Configuration file not found at {config_path}. Using an empty config.")
            self.CONFIG = {'gpt': {}} # Ensure CONFIG['gpt'] exists to avoid KeyErrors
        except Exception as e:
            logging.error(f"Failed to load or parse {config_path}: {e}")
            self.CONFIG = {'gpt': {}}

        # Use provided curated_lines or default to an empty list
        self.curated_lines = curated_lines or []
        self.max_retries = self.CONFIG.get('max_retries', 3)
        self.api_url = self.CONFIG.get('ollama_api_url', "http://localhost:11434/api/generate")

    def _build_prompt(self, bio_text: str) -> str:
        """
        Constructs a detailed prompt for the language model, encouraging specificity.

        This revised prompt asks the model to first identify a specific detail
        from the bio, which helps ground the generated message in something concrete,
        making it feel more personal and less generic.

        Args:
            bio_text (str): The user's bio text.

        Returns:
            str: The fully constructed prompt.
        """
        # Create a string of examples for the prompt
        examples = "\n".join(f"- {line}" for line in self.curated_lines)

        # The prompt is structured to guide the model's thought process.
        return f"""
        Write a flirty, funny, and simple opener that gets a reply. Focus on few interesting detail from her bio and ask a playful question or make a confident comment about it

        avoid making plans or activity with the person.

        Keep it under 100 characters

        Use natural punctuation like ?!,-

        Avoid starting sentences with -

        Don't make any plans or say “we should”

        Avoid emojis, quotes, or long sentences

        Don't greet her by name or say hello

        Keep it positive and easy to understand

        Do NOT suggest plans or shared activities, just a fun opener
        
        Avoid start with "If we matched," or similar phrases that imply a match is already made
        
        Avoid wingman lines, no "let's meet" or similar phrases
        
        Avoid lines that imply a match is already made

        Example: {examples}

        return only one best reponse 

        """
        # return f"""You're a witty, {self.CONFIG['gpt'].get('personality', 'charming and confident')} man, age 25 sending a fun, 
        # flirty and witty first message on a dating app. 

        # Their bio: "{bio_text}"

        # Your goal is to write a clever opener that gets a response.

        # **Thinking Steps:**
        # 0. **Pun**: If you can create a great pun about her name, we can also reply with it. pun should be funny and simple
        # 1.  **Analyze the Bio:** Read the bio carefully and pick out 2/3 specific, interesting detail.
        # 2.  **Brainstorm a Positive Angle:** Based on that one detail, think of a playful question or comment. **Crucially, frame it positively. select best one from it**  
        # 3.  **Draft the Message:** Write the message following all the rules below.
        # 4. **Recheck:** check if the person can start conversation from the generated message. if it is dead end don't create 

        # **Message Examples (Tone & Style):**
        # {examples if examples else "- So you're a fan of pineapple on pizza too huh"}

        # **Final Rules for the Output:**
        # - You must return ONLY the message text. No explanations or extra text.
        # - **Be positive and confident.** Avoid backhanded compliments or negging (e.g., "I'd like you if...").
        # - The message must be a single, complete sentence under 100 characters.
        # - Punctuation like '?!,- is allowed for a natural tone.
        # - NO emojis, quotes, or line breaks.
        # - Your response should be ready to be copied and pasted directly.
        # - Donot use the exact what is provided in the promt
        # - never make plans together on the first text
        # - keep it simple for humans to understand
        # - donot reply same text in the promt, make it different
        # - don't do hello person name
        # - make it in simple vocab.
        # - donot mae plans with her on the first go, like we can explore together or we can plan this together.

        # Now, based on the bio provided, generate the message. give only single response
        # """

    def _is_valid_message(self, message: str) -> bool:
        """
        Validates the generated message against a set of rules.

        This function is relaxed to allow for basic punctuation, which is crucial
        for creating a natural and expressive tone.

        Args:
            message (str): The message generated by the model.

        Returns:
            bool: True if the message is valid, False otherwise.
        """
        if not message:
            return False

        msg = message.strip()

        # Rule: Check character length
        if not (10 < len(msg) < 140):
            logging.warning(f"Validation Fail (Length): Message length is {len(msg)}. Message: '{msg}'")
            return False

        # Rule: Allow basic punctuation (including hyphens) but forbid other special characters.
        if not re.match(r"^[a-zA-Z0-9 .,!?'\-()]+$", msg):
            logging.warning(f"Validation Fail (Characters): Message contains invalid characters. Message: '{msg}'")
            return False
            
        # Rule: Check for obviously bad patterns or "hallucinations" from the model
        banned_patterns = [
            r"\n",                    # No line breaks
            r"bio:",                  # Shouldn't mention the bio directly
            r"\[.*\]",                # No markdown-style tags
            r"message:",              # Shouldn't say "message:"
            r"^(hi|hey|hello)\b",     # Avoid generic greetings
            r"\bif only you\b",       # Avoid backhanded compliments
        ]

        if any(re.search(pat, msg, re.IGNORECASE) for pat in banned_patterns):
            logging.warning(f"Validation Fail (Banned Pattern): Message contains a forbidden pattern. Message: '{msg}'")
            return False
            
        # Rule: Check if the message is a duplicate of an example
        if msg.lower() in [line.lower() for line in self.curated_lines]:
            logging.warning(f"Validation Fail (Duplicate): Message is a direct copy of an example. Message: '{msg}'")
            return False

        return True

    def _generate_raw_message(self, prompt: str) -> str | None:
        """
        Sends the prompt to the Ollama API and gets a raw response.

        Args:
            prompt (str): The prompt to send to the model.

        Returns:
            str or None: The stripped message text if successful, otherwise None.
        """
        try:
            # Using the requests.post method with a timeout is best practice
            res = requests.post(
                self.api_url,
                json={
                    "model": self.CONFIG['gpt'].get("model", "llama3.1:8b-instruct-q4_0"),
                    "prompt": prompt,
                    "stream": False, # Set to False for a single response object
                    "top_p": 0.9,
                    "temperature": self.CONFIG['gpt'].get("temperature", 0.2)
                    
                },
                timeout=60 # Add a timeout to prevent indefinite hanging
            )
            # Raise an exception for bad status codes (4xx or 5xx)
            res.raise_for_status()
            
            # Since stream=False, we can parse the JSON response directly
            response_data = res.json()
            message = response_data.get("response", "").strip()
            
            # Clean up potential leading/trailing quotes that models sometimes add
            return message.strip('"')

        except requests.exceptions.RequestException as e:
            logging.error(f"Ollama API request failed: {e}")
            return None
        except json.JSONDecodeError as e:
            logging.error(f"Failed to decode JSON from Ollama API: {e}")
            return None

    def generate(self, bio_text: str) -> str | None:
        """
        Generates a valid, high-quality message based on the bio text.

        It will attempt to generate a message up to `max_retries` times
        until a valid one is produced.

        Args:
            bio_text (str): The user's bio text.

        Returns:
            str or None: A valid message string, or None if no valid
                         message could be generated.
        """
        # Ensure bio_text is a non-empty string
        if not bio_text or not isinstance(bio_text, str):
            logging.warning("generate() called with invalid or empty bio_text.")
            return None

        prompt = self._build_prompt(bio_text)
        
        for attempt in range(self.max_retries):
            logging.info(f"Generating message... (Attempt {attempt + 1}/{self.max_retries})")
            
            message = self._generate_raw_message(prompt)
            
            if message and self._is_valid_message(message):
                logging.info(f"✅ Valid message generated: '{message}'")
                return message
            
            logging.warning(f"❌ Invalid message on attempt {attempt + 1}. Reason logged above. Retrying...")
            
        logging.error(f"Failed to generate a valid message after {self.max_retries} attempts.")
        return None


    def clean_prompt_text(self, raw_text, max_lines_per_prompt=3, min_ratio=0.9):
        """
        Cleans OCR output and matches against known prompt list.
        
        Args:
            raw_text (str): The raw OCR output (from Tesseract)
            known_prompts (List[str]): Clean prompt library (flat list of full prompts)
            max_lines_per_prompt (int): How many OCR lines to group when trying to match a prompt
            min_ratio (float): Matching similarity threshold (0-1)
        
        Returns:
            List[str]: Cleaned list of matched or plausible prompts
        """
        known_prompts = self.load_known_prompts("utils/allPromts.txt")
        try:
            lines = [l.strip() for l in raw_text.splitlines() if l.strip()]
            
            # Remove noisy timestamps or patterns like "730 ee"
            lines = [l for l in lines if not re.match(r'^[\d\s:]{2,}.*$', l) and not re.search(r'\b(?:ee|am|pm)\b', l, re.IGNORECASE)]
            
            cleaned_prompts = []
            i = 0
            while i < len(lines):
                # Try to group 1 to max_lines_per_prompt together
                for j in range(max_lines_per_prompt, 0, -1):
                    chunk = " ".join(lines[i:i+j])
                    match = self.find_best_match(chunk, known_prompts, min_ratio)
                    if match:
                        cleaned_prompts.append(match)
                        i += j
                        break
                else:
                    # No good match, move ahead by 1 line
                    i += 1
            
            return cleaned_prompts

        except Exception as e:
            logging.error(f"Error cleaning prompt text: {e}")
            return []

    def find_best_match(self, chunk, known_prompts, threshold):
        """
        Finds the best match from known prompts using string similarity.
        """
        chunk = chunk.lower()
        best_ratio = 0
        best_match = None
        for prompt in known_prompts:
            ratio = SequenceMatcher(None, chunk, prompt.lower()).ratio()
            if ratio > best_ratio and ratio >= threshold:
                best_ratio = ratio
                best_match = prompt
        return best_match

    def load_known_prompts(self, filepath):
        prompts = []
        with open(filepath, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line and not re.match(r"^\d+\.", line):  # skip section headers
                    prompts.append(line)
        return prompts
