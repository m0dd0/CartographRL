# import gymnasium as gym

# from .general import InvalidMoveError, CardDeck
# from .scoring import ScoringDeck
# from .map import Map


# class CarthographersEnv(gym.Env):
#     metadata = {"render.modes": ["human"]}

#     def __init__(
#         self,
#         scoring_deck: ScoringDeck,
#         exploration_deck: CardDeck,
#         map_sheet: Map,
#         season_times: Tuple[int, int, int, int] = (8, 8, 7, 6),
#         render_mode: str = None,
#     ):
#         self.map_sheet = map_sheet
#         self.exploration_deck = exploration_deck
#         self.scoring_cards = scoring_deck.draw()
#         self.season_times = season_times

#         assert render_mode is None or render_mode in self.metadata["render_modes"]
#         self.render_mode = render_mode

#         self.observation_space = gym.spaces.Dict(
#             {
#                 "map": gym.spaces.Box(low=1, high=size, dtype=int),
#                 "season": gym.spaces.Discrete(4),
#                 "time": gym.spaces.Discrete(8),
#                 "exploration_card": gym.spaces.Discrete(
#                     len(self.exploration_card_stack)
#                 ),
#                 # TODO make the exploration card observation a 2d space
#                 "exploration_card_setable": gym.spaces.Discrete(2),
#                 # task1
#                 # task2
#                 # task3
#                 # task4
#                 # map_type
#             }
#         )

#         self.action_space = gym.spaces.Dict(
#             {
#                 "option": gym.spaces.Discrete(5),
#                 "position": gym.spaces.Box(low=0, high=size, dtype=int),
#                 "rotation": gym.spaces.Discrete(4),
#                 "single_field": gym.spaces.Discrete(5),
#             }
#         )

#         self.invalid_move_reward = -1000

#         self._map = None
#         self._season = None
#         self._time = None
#         self._coins = None
#         self._surrounded_mountains = None

#         self.ruin = False
#         self.exploration_card = None

#     def _set_monster(self, monster_card):
#         # TODO
#         pass

#     def step(self, action):
#         if len(self.exploration_card.options) - 1 < action["option"]:
#             return (self.invalid_move_reward,)

#         try:
#             self.map.place(
#                 self.exploration_card.options[action["option"]],
#                 action["rotation"],
#                 action["position"],
#                 on_ruin=self.ruin,
#             )
#         except InvalidMoveError:
#             return (self.invalid_move_reward,)

#         if self.exploration_card.options[action["option"]].coin:
#             self._coins += 1

#         self.exploration_card = None
#         self.ruin = False

#         self._time += self.exploration_card.time

#         if self._time >= self.season_times[self._season]:
#             surrounded_mountains = self.map.surrounded_mountains()
#             self.coins += surrounded_mountains - self._surrounded_mountains
#             self._surrounded_mountains = surrounded_mountains
#             if self._season == 0:
#                 score = self.task_A.evaluate(self.map) + self.task_B.evaluate(self.map)
#             elif self._season == 1:
#                 score = self.task_B.evaluate(self.map) + self.task_C.evaluate(self.map)
#             elif self._season == 2:
#                 score = self.task_C.evaluate(self.map) + self.task_D.evaluate(self.map)
#             elif self._season == 3:
#                 score = self.task_D.evaluate(self.map) + self.task_A.evaluate(self.map)

#             score += self.coins - self.map.evla_monsters()

#             self._season += 1
#             self._time = 0

#         while self.exploration_card is None:
#             drawn_card = self.exploration_card_stack.draw()
#             if isinstance(drawn_card, RuinCard):
#                 self.ruin = True
#             elif isinstance(drawn_card, MonsterCard):
#                 self._set_monster(drawn_card)
#             elif isinstance(drawn_card, ExplorationCard):
#                 self.exploration_card = drawn_card

#         return

#     def reset(self):
#         self._map = None
#         self._season = 0
#         self._time = 0

#         self.task1 = ScoringCard()
#         self.task2 = ScoringCard()
#         self.task3 = ScoringCard()
#         self.task4 = ScoringCard()
