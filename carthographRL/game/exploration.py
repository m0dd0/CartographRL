from typing import List, Tuple
from enum import Enum

import numpy as np

from .general import Card, Terrains


class ExplorationOption(Card):
    coin: bool
    coords: List[Tuple[int, int]]
    terrain: Terrain


class ExplorationCard(Card):
    name: str
    card_id: int
    time: int
    options: List[ExplorationOption]


class MonsterCorner(Enum):
    TOP_LEFT = 1
    TOP_RIGHT = 2
    BOTTOM_LEFT = 3
    BOTTOM_RIGHT = 4


class MonsterRotation(Enum):
    CLOCKWISE = 1
    COUNTER_CLOCKWISE = 2


class MonsterCard(Card):
    name: str
    card_id: int
    position: MonsterCorner
    rotation: MonsterRotation


class RuinCard(Card):
    name: str
    card_id: int


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

RUIN_CARDS = [
    RuinCard(name="Verfallenert Außernposeten", card_id=106),
    RuinCard(name="Tempelruinen", card_id=105),
]


class ExplorationDeck:
    def _filter_heroes(self, cards, heroes: bool):
        if heroes:
            return cards
        else:
            return [c for c in cards if not c.is_hero()]

    def __init__(
        self,
        heroes: bool = False,
        n_ruins: int = None,
        n_monsters: int = None,
        rng: np.random.Generator = None,
    ):
        exploration_cards = self._filter_heroes(EXPLORATION_CARDS, heroes)
        ruin_cards = self._filter_heroes(RUIN_CARDS, heroes)
        monster_cards = self._filter_heroes(MONSTER_CARDS, heroes)

        if rng is None:
            rng = np.random.default_rng()

        if n_ruins is not None:
            ruin_cards = rng.choice(ruin_cards, n_ruins, replace=False).tolist()
        if n_monsters is not None:
            monster_cards = rng.choice(
                monster_cards, n_monsters, replace=False
            ).tolist()

        self._cards = exploration_cards + ruin_cards + monster_cards

        rng.shuffle(self._cards)

    def draw(self) -> Card:
        return self._cards.pop()
