from typing import Tuple

from ..model import CarthographersGame
from ..model.general import Terrains
from .base import View


class PygameView(View):
    def __init__(self):
        pass

    def render(self, game: CarthographersGame):
        pass

    def get_action(self) -> Tuple[int, Tuple[int, int], int, bool, Terrains]:
        pass
