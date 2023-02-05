import gymnasium as gym


class CarthographersEnv(gym.Env):
    metadata = {"render.modes": ["human"]}

    def __init__(self, render_mode=None, size: int = 11):
        #  def __init__(self, map, scoring_card_stack, exploration_card_stack):
        self.map = map
        self.scoring_card_stack = scoring_card_stack
        self.exploration_card_stack = exploration_card_stack

        self.tasks = self.scoring_card_stack.draw()

        self.season_times = (8, 8, 7, 6)
        assert render_mode is None or render_mode in self.metadata["render_modes"]
        self.render_mode = render_mode

        self.observation_space = gym.spaces.Dict(
            {
                "map": gym.spaces.Box(low=1, high=size, dtype=int),
                "season": gym.spaces.Discrete(4),
                "time": gym.spaces.Discrete(8),
                # task1
                # task2
                # task3
                # task4
                # map_type
            }
        )

        self.action_space = gym.spaces.Dict(
            {
                "option": gym.spaces.Discrete(5),
                "position": gym.spaces.Box(low=0, high=size, dtype=int),
                "rotation": gym.spaces.Discrete(4),
            }
        )

        self.invalid_move_reward = -1000

        self._map = None
        self._season = None
        self._time = None

        self.ruin = False
        self.exploration_card = None

    def _set_monster(self, monster_card):
        # TODO
        pass

    def step(self, action):
        if len(self.exploration_card.options) - 1 < action["option"]:
            return (self.invalid_move_reward,)

        # ruin = False

        # drawn_card = self.exploration_card_stack.draw()
        # exploration_card = None
        # while exploration_card is None:
        #     if isinstance(drawn_card, RuinCard):
        #         ruin = True
        #     elif isinstance(drawn_card, MonsterCard):
        #         self._set_monster(drawn_card)
        #     elif isinstance(drawn_card, ExplorationCard):
        #         exploration_card = drawn_card

    def reset(self):
        self._map = None
        self._season = 0
        self._time = 0

        self.task1 = ScoringCard()
        self.task2 = ScoringCard()
        self.task3 = ScoringCard()
        self.task4 = ScoringCard()
