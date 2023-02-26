from matplotlib import pyplot as plt

from .game import CarthographersGame


class AsciiRenderer:
    def __init__(self):
        pass

    def _render_scoring_card(self, card):
        return f"[{card.task_type.name}] {card.name}: {card.description}"

    def _render_exploration_card(self, card):
        output = ""
        output += f"{card.name} [{card.time}] (id: {card.id})\n"

    def __call__(self, game: CarthographersGame):
        output = ""
        output += f"Task A: {self._render_scoring_card(game.scoring_cards[0])}\n"
        output += f"Task B: {self._render_scoring_card(game.scoring_cards[1])}\n"
        output += f"Task C: {self._render_scoring_card(game.scoring_cards[2])}\n"
        output += f"Task D: {self._render_scoring_card(game.scoring_cards[3])}\n"
        output += "\n"
        output += f"Season: {game.season} -- Time: {game.time}/{game.season_times[game.season]}\n"
        output += f"Coins: {game.coins}\n"
        output += "\n"
        output += f"Exploration card: {game.exploration_card.name}\n"


class MplRenderer:
    def __init__(self):
        pass

    def __call__(self, game: CarthographersGame):
        plt.matshow(game.map_sheet.terrain_map)
        plt.show()
