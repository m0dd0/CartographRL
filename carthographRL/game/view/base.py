from abc import ABC, abstractmethod
from typing import Tuple
from pathlib import Path

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

def get_asset_path(image_name: str):
    """Get the path to an asset.

    Args:
        image_name (str): Name of the asset.

    Returns:
        Path: Path to the asset.
    """
    if image_name is None:
        return None
    return Path(__file__).parent / "assets" / image_name