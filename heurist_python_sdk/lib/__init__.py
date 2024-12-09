import os
from typing import Optional, Union


def read_env(env: str) -> Optional[Union[str, None]]:
    value = os.environ.get(env)
    return value.strip() if value else None
