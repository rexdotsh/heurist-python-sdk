import random
import string


def generate_random_hex(length: int) -> str:
    hex_chars = string.hexdigits.lower()[:16]  # 0-9a-f only
    return "".join(random.choice(hex_chars) for _ in range(length))
