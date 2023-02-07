from .general import InvalidMoveError, CardDeck
from .scoring import ScoringDeck
from .map import Map
from .exploration import ExplorationCard, ExplorationOption, RuinCard, MonsterCard


class CarthographersEnv:
    def __init__(
        self,
        scoring_deck: ScoringDeck,
        exploration_deck: CardDeck,
        map_sheet: Map,
        season_times: Tuple[int, int, int, int] = (8, 8, 7, 6),
    ):
        # game setup
        self.exploration_deck = exploration_deck
        self.scoring_cards = scoring_deck.draw()
        self.season_times = season_times

        # state of the game
        self.map_sheet = map_sheet
        self.season = 0
        self.time = 0
        self.coins = 0
        self.ruin = False
        self.score = 0
        self.exploration_card = self.exploration_deck.draw()

    def _set_monster(self, monster_card: MonsterCard):
        # TODO
        pass

    def play(self, i_option, position, rotation, single_field):
        # TODO account for mirroring option
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
                on_ruin=self.ruin,
            )
        else:
            self.map.place(
                ExplorationOption(coin=False, coords=[(0, 0)], terrain=single_field),
                0,
                position,
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

    def rener(self) -> str:
        # TODO
        pass
