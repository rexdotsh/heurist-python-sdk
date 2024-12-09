from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from . import Heurist


class APIResource:
    def __init__(self, client: "Heurist"):
        self._client: "Heurist" = client
