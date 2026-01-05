import os
import logging
from dotenv import load_dotenv
from crewai import LLM


# Load environment variables
load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize Gemini LLM with robust error handling
try:
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("GEMINI_API_KEY not found in environment variables")

    os.environ["GOOGLE_API_KEY"] = api_key

    llm = LLM(
        model='gemini/gemini-2.0-flash-lite',
        api_key=api_key,
        temperature=0.5,  # Lower temperature for higher consistency and professionalism.
        max_tokens=160
    )
    logger.info("LLM initialized successfully with Gemini 2.0 Flash Lite")
except Exception as e:
    logger.error(f"Failed to initialize LLM: {str(e)}")
    raise Exception(f"LLM initialization failed: {str(e)}")
