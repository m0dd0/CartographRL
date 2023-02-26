from enum import Enum
from typing import List, Tuple

import numpy as np

from .general import InvalidMoveError, CardDeck, MonsterMode
from .scoring import ScoringDeck, SCORING_CARDS
from .map import Map
from .exploration import (
    ExplorationCard,
    ExplorationOption,
    RuinCard,
    MonsterCard,
    EXPLORATION_CARDS,
    MONSTER_CARDS,
    RUIN_CARDS,
)


class CarthographersGame:
    def __init__(
        self,
        scoring_deck: ScoringDeck = None,
        exploration_deck: CardDeck = None,
        map_sheet: Map = None,
        season_times: Tuple[int, int, int, int] = (8, 8, 7, 6),
        monster_mode: MonsterMode = MonsterMode.RANDOM,
        rng: np.random.Generator = None,
    ):
        # game setup
        self.exploration_deck = exploration_deck or CardDeck(
            EXPLORATION_CARDS + MONSTER_CARDS + RUIN_CARDS
        )
        scoring_deck = scoring_deck or ScoringDeck(SCORING_CARDS)
        self.scoring_cards = scoring_deck.draw()
        self.season_times = season_times
        self.monster_mode = monster_mode
        self.rng = rng or np.random.default_rng()

        # state of the game
        self.map_sheet = map_sheet or Map.generate_A()
        self.season = 0
        self.time = 0
        self.coins = 0
        self.ruin = False
        self.score = 0
        self.exploration_card = self.exploration_deck.draw()

    def _set_monster_random(self, coords):
        setable_options = list(self.map_sheet.setable_options(coords, on_ruin=False))
        opt = self.rng.choice(setable_options)
        self.map_sheet.place(coords, *opt, on_ruin=False)

    def _set_monster_solo(self, coords):
        raise NotImplementedError()

    def _set_monster_max_borders(self, coords):
        setable_options = list(self.map_sheet.setable_options(coords, on_ruin=False))

        n_empty_max = 0
        best_opt = None
        for opt in setable_options:
            map_coords = self.map_sheet.transform_to_map_coords(
                coords, rotation, position, mirror
            )
            n_empty = np.sum(
                Cluster(map_coords).surrounding_terrains() == Terrain.EMPTY.value
            )
            if n_empty >= n_empty_max:
                n_empty_max = n_empty
                best_option = opt

        self.map_sheet.place(monster_card.coords, *best_option, on_ruin=False)

    def _set_monster(self, monster_card: MonsterCard):
        coords = np.array(monster_card.coords)
        if not self.map_sheet.is_setable(monster_card.coords, on_ruin=False):
            coords = np.array([[0, 0]])

        if self.monster_mode == MonsterMode.RANDOM:
            self._set_monster_random(coords)

        elif self.monster_mode == MonsterMode.SOLO:
            self._set_monster_solo(coords)

        elif self.monster_mode == MonsterMode.MAX_BORDERS:
            self._set_monster_max_borders(coords)

    def play(self, i_option, position, rotation, mirror, single_field):
        if len(self.exploration_card.options) < option:
            raise InvalidMoveError("Invalid option")

        if single_field is not None and any(
            self.map_sheet.is_setable(opt, self.on_ruin)
            for opt in self.exploration_card.options
        ):
            raise InvalidMoveError("There is a possibility to set one of the options.")

        exploration_option = exploration_card.options[i_option]

        surrounded_mountains_prev = self.map.surrounded_mountains()

        if not single_field:
            self.map.place(
                self.exploration_card.options[option],
                rotation,
                position,
                mirror,
                on_ruin=self.ruin,
            )
        else:
            self.map.place(
                ExplorationOption(coin=False, coords=[(0, 0)], terrain=single_field),
                0,
                position,
                mirror,
                on_ruin=False,
            )

        if single_field is None and exploration_option.coin:
            self.coins += 1
        self.coins += self.map.surrounded_mountains() - surrounded_mountains_prev

        self.time += self.exploration_card.time

        self.exploration_card = None
        self.ruin = False

        if self.time >= self.season_times[self.season]:
            season_score = self.coins - self.map.eval_monsters()

            season_score += self.scoring_cards[self.season].evaluate(self.map)
            season_score += self.scoring_cards[
                (self.season + 1) % len(self.season)
            ].evaluate(self.map)

            self.season += 1
            self.time = 0

        while self.exploration_card is None:
            drawn_card = self.exploration_card_stack.draw()
            if isinstance(drawn_card, RuinCard):
                self.ruin = True
            elif isinstance(drawn_card, MonsterCard):
                self._set_monster(drawn_card)
            elif isinstance(drawn_card, ExplorationCard):
                self.exploration_card = drawn_card

    # def render(self) -> str:
    #     self.rendere
    #     # TODO pygame
    #     # TODO MVC pattern --> use Display class
    #     output = ""
    #     output += f"Task A: {self.scoring_cards[0].}"
    #     output += f"Season: {self.season}"
    #     output += f"Time: {self.time}"
    #     output += f"Coins: {self.coins}"
    #     output += f"Score: {self.score}"
    #     output += f"Ruin: {self.ruin}"
    #     output += f"Exploration card: {self.exploration_card}"
    #     output += f"Map: {self.map}"
    #     return output
