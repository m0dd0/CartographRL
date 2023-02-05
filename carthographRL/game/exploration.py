from dataclasses import dataclass
from typing import List, Tuple

from .terrains import Terrain
from .general import MonsterCorner, MonsterRotation


@dataclass
class ExplorationOption:
    coin: bool
    coords: List[Tuple[int, int]]
    terrain: Terrain


@dataclass
class ExplorationCard:
    name: str
    card_id: int
    time: int
    options: List[ExplorationOption]

    def is_hero(self):
        if self.card_id % 100 == 1:
            return False
        elif self.card_id % 100 == 2:
            return True
        else:
            raise ValueError("Card ID is invalid.")


@dataclass
class MonsterCard:
    name: str
    card_id: int
    position: MonsterCorner
    rotation: MonsterRotation


# class Season:
#     # @classmethod
#     # def generate_spring(cls):
#     #     return cls(
#     #         name="Frühling",

#     def __init__(self, name, time, tasks):
#         self.name = name
#         self.time = time
#         assert len(tasks) == 2
#         self.tasks = tasks


EXPLORATION_CARDS = [
    ExplorationCard(
        name="Großer Strom",
        card_id=107,
        time=1,
        options=[
            ExplorationOption(
                coin=True, coords=[(0, 0), (1, 0), (2, 0)], terrain=Terrain.WATER
            ),
            ExplorationOption(
                coin=False,
                coords=[(0, 2), (1, 1), (1, 2), (2, 0), (2, 1)],
                terrain=Terrain.WATER,
            ),
        ],
    ),
    ExplorationCard(
        name="Ackerland",
        card_id=108,
        time=1,
        options=[
            ExplorationOption(coin=True, coords=[(0, 0), (1, 0)], terrain=Terrain.FARM),
            ExplorationOption(
                coin=False,
                coords=[(0, 1), (1, 0), (1, 1), (1, 2), (2, 1)],
                terrain=Terrain.FARM,
            ),
        ],
    ),
    ExplorationCard(
        name="Weiler",
        card_id=109,
        time=1,
        options=[
            ExplorationOption(
                coin=True, coords=[(0, 0), (1, 0), (1, 1)], terrain=Terrain.VILLAGE
            ),
            ExplorationOption(
                coin=False,
                coords=[(0, 0), (0, 1), (0, 2), (1, 0), (1, 1)],
                terrain=Terrain.VILLAGE,
            ),
        ],
    ),
    ExplorationCard(
        name="Vergessener Wald",
        card_id=110,
        time=1,
        options=[
            ExplorationOption(
                coin=True, coords=[(0, 0), (1, 1)], terrain=Terrain.FOREST
            ),
            ExplorationOption(
                coin=False,
                coords=[(0, 0), (1, 0), (1, 1), (2, 1)],
                terrain=Terrain.FOREST,
            ),
        ],
    ),
    ExplorationCard(
        name="Sumpf",
        card_id=115,
        time=2,
        options=[
            ExplorationOption(
                coin=False,
                coords=[(0, 0), (1, 0), (1, 1), (1, 2), (2, 0)],
                terrain=Terrain.WATER,
            ),
            ExplorationOption(
                coin=False,
                coords=[(0, 0), (1, 0), (1, 1), (1, 2), (2, 0)],
                terrain=Terrain.FOREST,
            ),
        ],
    ),
    ExplorationCard(
        name="Obsthain",
        card_id=113,
        time=2,
        options=[
            ExplorationOption(
                coin=False,
                coords=[(0, 0), (0, 1), (0, 2), (1, 2)],
                terrain=Terrain.FARM,
            ),
            ExplorationOption(
                coin=False,
                coords=[(0, 0), (0, 1), (0, 2), (1, 2)],
                terrain=Terrain.FOREST,
            ),
        ],
    ),
    ExplorationCard(
        name="Baumwipfeldorf",
        card_id=114,
        time=2,
        options=[
            ExplorationOption(
                coin=False,
                coords=[(0, 2), (0, 3), (1, 0), (1, 1), (1, 2)],
                terrain=Terrain.VILLAGE,
            ),
            ExplorationOption(
                coin=False,
                coords=[(0, 2), (0, 3), (1, 0), (1, 1), (1, 2)],
                terrain=Terrain.FOREST,
            ),
        ],
    ),
    ExplorationCard(
        name="Hinterlandbach",
        card_id=111,
        time=2,
        options=[
            ExplorationOption(
                coin=False,
                coords=[(0, 0), (0, 1), (0, 2), (1, 0), (2, 0)],
                terrain=Terrain.WATER,
            ),
            ExplorationOption(
                coin=False,
                coords=[(0, 0), (0, 1), (0, 2), (1, 0), (2, 0)],
                terrain=Terrain.FARM,
            ),
        ],
    ),
    ExplorationCard(
        name="Gehöft",
        card_id=112,
        time=2,
        options=[
            ExplorationOption(
                coin=False,
                coords=[(0, 0), (1, 0), (1, 1), (2, 0)],
                terrain=Terrain.VILLAGE,
            ),
            ExplorationOption(
                coin=False,
                coords=[(0, 0), (1, 0), (1, 1), (2, 0)],
                terrain=Terrain.FARM,
            ),
        ],
    ),
    ExplorationCard(
        name="Fischerdorf",
        card_id=116,
        time=2,
        options=[
            ExplorationOption(
                coin=False,
                coords=[(0, 0), (0, 1), (0, 2), (0, 3)],
                terrain=Terrain.VILLAGE,
            ),
            ExplorationOption(
                coin=False,
                coords=[(0, 0), (0, 1), (0, 2), (0, 3)],
                terrain=Terrain.WATER,
            ),
        ],
    ),
    ExplorationCard(
        name="Splitterland",
        card_id=117,
        time=0,
        options=[
            ExplorationOption(coin=False, coords=[(0, 0)], terrain=Terrain.FOREST),
            ExplorationOption(coin=False, coords=[(0, 0)], terrain=Terrain.FARM),
            ExplorationOption(coin=False, coords=[(0, 0)], terrain=Terrain.VILLAGE),
            ExplorationOption(coin=False, coords=[(0, 0)], terrain=Terrain.WATER),
            ExplorationOption(coin=False, coords=[(0, 0)], terrain=Terrain.DEVIL),
        ],
    ),
]

MONSTER_CARDS = [
    MonsterCard(
        name="Grottenschratüberfall",
        card_id=102,
        position=MonsterCorner.TOP_RIGHT,
        rotation=MonsterRotation.CLOCKWISE,
    ),
    MonsterCard(
        name="Goblinattacke",
        card_id=101,
        position=MonsterCorner.BOTTOM_LEFT,
        rotation=MonsterRotation.COUNTER_CLOCKWISE,
    ),
    MonsterCard(
        name="Koboldansturm",
        card_id=103,
        position=MonsterCorner.BOTTOM_LEFT,
        rotation=MonsterRotation.CLOCKWISE,
    ),
    MonsterCard(
        name="Gnollangriff",
        card_id=104,
        position=MonsterCorner.TOP_LEFT,
        rotation=MonsterRotation.COUNTER_CLOCKWISE,
    ),
]


class ExplorationCardStack:
    def __init__(self, heroes: bool = False):
        self._cards = [c for c in EXPLORATION_CARDS if heroes or not c.is_hero()]
