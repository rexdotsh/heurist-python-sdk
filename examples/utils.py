import os
import random
import string
from pathlib import Path

from dotenv import load_dotenv


def load_env():
    """Load environment variables from .env file in the current directory"""
    env_path = Path(__file__).parent / ".env"
    load_dotenv(env_path)

    # Verify API key is present
    api_key = os.getenv("HEURIST_API_KEY")
    if not api_key or api_key == "your-api-key-here":
        raise ValueError("Please set your HEURIST_API_KEY in the .env file")


def generate_random_hex(length: int) -> str:
    hex_chars = string.hexdigits.lower()[:16]  # 0-9a-f only
    return "".join(random.choice(hex_chars) for _ in range(length))
