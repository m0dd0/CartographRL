from abc import ABC, abstractmethod
from typing import Tuple

from ..model import CarthographersGame
from ..model.general import Terrains


class View(ABC):
    def __init__(self):
        self._closed = False

    @abstractmethod
    def render(
        self, game: CarthographersGame
    ) -> Tuple[int, Tuple[int, int], int, bool, Terrains]:
        pass

    @abstractmethod
    def cleanup(self):
        pass

    @property
    def closed(self):
        return self._closed
