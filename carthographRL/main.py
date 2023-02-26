from carthographRL.game import CarthographersGame
from carthographRL.game.render import MplRenderer


def main():
    renderer = MplRenderer()
    game = CarthographersGame()

    renderer(game)


if __name__ == "__main__":
    main()
