from carthographRL.game.model import CarthographersGame
from carthographRL.game.view import PygameView
from carthographRL.game.controller import Controller


def main():
    game = CarthographersGame()
    view = PygameView(game.map_sheet.size)
    controller = Controller(game, view)
    controller.run()


if __name__ == "__main__":
    main()
