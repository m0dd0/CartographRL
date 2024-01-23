"""This implementation is kepp as simple as possible to allow for easy testing of the environment.
It does not include any performance optimizations."""

from typing import List
import random

from cartographRL.model.cartographers_base_model import (
    CartographersBaseModel,
    Map,
    ScoringCard,
    ExplorationCard,
    ExplorationOption,
    Terrains,
)


class Cartographers(CartographersBaseModel):
    def __init__(
        self,
        map: Map,
        scoring_cards: List[ScoringCard],
        exploration_cards: List[ExplorationCard],
        season_times: List[int],
    ):
        super().__init__(map, scoring_cards, exploration_cards, season_times)

        self._current_season = 0
        self._current_time = 0
        self._exploration_cards = random.sample(
            exploration_cards, len(exploration_cards)
        )
        self._current_exploration_options = self._exploration_cards.pop().options
        self._is_game_over = False
        self._score = 0

    @property
    def current_season(self) -> int:
        return self._current_season

    @property
    def current_time(self) -> int:
        return self._current_time

    @property
    def current_exploration_options(self) -> List[ExplorationOption]:
        return self._current_exploration_options

    @property
    def is_game_over(self) -> bool:
        return self._is_game_over

    @property
    def current_score(self) -> int:
        return self._score

    def _transform_shape(
        self,
        shape: List[List[bool]],
        rotation: int,
        flip: bool,
    ) -> List[List[bool]]:
        new_shape = []
        if rotation = 0:
            new_shape = exploration_option.shape
        # elif rotation = 1:
        #     for y, row in enumerate(exploration_option.shape):
        #         for x, cell in enumerate(row):
        #             new_shape[x][y] = cell
        # elif rotation = 2:
        #     for y, row in enumerate(exploration_option.shape):
        #         for x, cell in enumerate(row):
        #             new_shape[x][y] = cell
        return new_shape

    def is_playable(
        self,
        exploration_option: ExplorationOption,
        x: int,
        y: int,
        rotation: int,
        flip: bool,
    ) -> bool:
        transformed_shape = self._transform_exploration_option(
            exploration_option, rotation, flip
        )
        for y_new, new_row in enumerate(exploration_option.shape):
            for x_new, new_cell in enumerate(new_row):
                if not new_cell:
                    continue

                if rotation == 1:
                    x_new, y_new = y_new, -x_new + exploration_option.shape.width - 1
                elif rotation == 2:
                    x_new, y_new = (
                        -x_new + exploration_option.shape.width - 1,
                        -y_new + exploration_option.shape.height - 1,
                    )
                elif rotation == 3:
                    x_new, y_new = -y_new + exploration_option.shape.height - 1, x_new
                if flip:
                    x_new = -x_new + exploration_option.shape.width - 1
                if not self.map[y + y_new][x + x_new] == Terrains.EMPTY:
                    return False

        return True

    def play(
        self,
        exploration_option: ExplorationOption,
        x: int,
        y: int,
        rotation: int,
        flip: bool,
    ):
        assert exploration_option in self._current_exploration_options
        assert self.is_playable(exploration_option, x, y, rotation, flip)

        self._current_time += exploration_option.time
        if self._current_time >= self._season_times[self._current_season]:
            self._current_time = 0
            self._current_season += 1
        self._current_exploration_options = self._exploration_cards.pop().options
