from abc import ABC, abstractmethod
from typing import Tuple

from ..model import CarthographersGame
from ..model.general import Terrains


class View(ABC):
    def __init__(self):
        pass

    @abstractmethod
    def render(self, game: CarthographersGame):
        pass

    @abstractmethod
    def get_action(self) -> Tuple[int, Tuple[int, int], int, bool, Terrains]:
        pass
