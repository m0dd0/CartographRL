from abc import ABC, abstractmethod
from typing import List
from enum import Enum
import importlib

from pydantic import BaseModel, validator, conlist, PositiveInt


class Terrains(Enum):
    EMPTY = " "
    WASTELAND = "X"
    WATER = "W"
    FOREST = "F"
    MOUNTAIN = "M"
    FIELD = "L"
    VILLAGE = "V"
    AMBUSH = "A"


class Rotation(Enum):
    CLOCKWISE = "C"
    COUNTERCLOCKWISE = "CC"


class TaskType(Enum):
    VILLAGE = "V"
    WATER_AND_FARMS = "WL"
    FOREST = "F"
    GEOMETRY = "G"


class AmbushCorner(Enum):
    TOP_LEFT = "TL"
    TOP_RIGHT = "TR"
    BOTTOM_LEFT = "BL"
    BOTTOM_RIGHT = "BR"


class Map(BaseModel):
    name: str
    fields: List[List[Terrains]]
    ruins: List[List[bool]]

    @validator("fields")
    @classmethod
    def field_must_be_rectangle(cls, fields):
        if not all(len(row) == len(fields[0]) for row in fields):
            raise ValueError("Fields must be rectangular")
        return fields

    @validator("ruins")
    @classmethod
    def ruins_must_be_rectangle(cls, ruins):
        if not all(len(row) == len(ruins[0]) for row in ruins):
            raise ValueError("Ruins must be rectangular")
        return ruins

    @validator("ruins")
    @classmethod
    def ruins_must_be_same_size(cls, ruins, values):
        if len(ruins) != len(values["fields"]) or len(ruins[0]) != len(
            values["fields"][0]
        ):
            raise ValueError("Ruins must be same size as fields")
        return ruins


class Card(BaseModel, ABC):
    name: str
    card_id: int


class ExplorationOption(BaseModel):
    coin: bool
    shape: List[List[bool]]
    terrain: Terrains

    @validator("shape")
    @classmethod
    def shape_must_be_rectangle(cls, shape):
        if not all(len(row) == len(shape[0]) for row in shape):
            raise ValueError("Shape must be rectangular")
        return shape


class ExplorationCard(Card):
    time: PositiveInt
    options: conlist(ExplorationOption, min_items=1, max_items=5)


class AmbushCard(Card):
    rotation: Rotation
    corner: AmbushCorner
    shape: List[List[bool]]

    @validator("shape")
    @classmethod
    def shape_must_be_rectangle(cls, shape):
        if not all(len(row) == len(shape[0]) for row in shape):
            raise ValueError("Shape must be rectangular")
        return shape


class RuinCard(Card):
    pass


class ScoringCard(Card):
    task_type: TaskType
    solo_points: PositiveInt
    description: str
    evaluation_function: str
    solo_points: PositiveInt

    @validator("evaluation_function")
    @classmethod
    def evaluation_function_must_be_defined(cls, evaluation_function):
        # check that a function with this name exists in the scoring_functions module
        scoring_functions = importlib.import_module(
            "cartographRL.model.game_assets.scoring_functions"
        )
        if not hasattr(scoring_functions, evaluation_function):
            raise ValueError(
                f"Scoring function {evaluation_function} does not exist in scoring_functions"
            )
        return evaluation_function


class CartographersBaseModel(ABC):
    def __init__(
        self,
        map: Map,
        scoring_cards: List[ScoringCard],
        exploration_cards: List[ExplorationCard],
        ambush_cards: List[AmbushCard],
        ruin_cards: List[RuinCard],
        season_times: List[int],
    ):
        assert len(scoring_cards) == len(
            season_times
        ), "Scoring cards and season times must have the same length"

        self._map = map
        self._scoring_cards = scoring_cards
        self._all_exploration_cards = exploration_cards
        self._all_ambush_cards = ambush_cards
        self._all_ruin_cards = ruin_cards
        self._season_times = season_times

    @property
    def map(self) -> Map:
        return self._map

    @property
    def scoring_cards(self) -> List[ScoringCard]:
        return self._scoring_cards

    @property
    def all_exploration_cards(self) -> List[ExplorationCard]:
        return self._all_exploration_cards

    @property
    def all_ambush_cards(self) -> List[AmbushCard]:
        return self._all_ambush_cards

    @property
    def all_ruin_cards(self) -> List[RuinCard]:
        return self._all_ruin_cards

    @property
    def season_times(self) -> List[int]:
        return self._season_times

    @property
    @abstractmethod
    def current_season(self) -> int:
        raise NotImplementedError

    @property
    @abstractmethod
    def current_time(self) -> int:
        raise NotImplementedError

    @property
    @abstractmethod
    def current_exploration_options(self) -> List[ExplorationOption]:
        raise NotImplementedError

    @property
    @abstractmethod
    def is_game_over(self) -> bool:
        raise NotImplementedError

    @abstractmethod
    def calculate_score(self) -> int:
        raise NotImplementedError

    # @abstractmethod
    # def is_playable(
    #     self,
    #     exploration_option: ExplorationOption,
    #     x: int,
    #     y: int,
    #     rotation: int,
    #     flip: bool,
    # ) -> bool:
    #     raise NotImplementedError

    @abstractmethod
    def play(
        self,
        exploration_option: ExplorationOption,
        x: int,
        y: int,
        rotation: int,
        flip: bool,
    ):
        raise NotImplementedError
