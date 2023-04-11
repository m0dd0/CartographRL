from .model import CarthographersGame
from .view.base import View


class Controller:
    def __init__(self, model: CarthographersGame, view: View):
        self.model = model
        self.view = view

    def run(self):
        while not self.view.closed:
            self.view.render(self.model)
            action = self.view.get_action()
            if action is not None:
                self.model.play(*action)


# pg.init()
# screen = pg.display.det_mode((800,400))
# clock = pg.

# while True:


# class GameController:
#     def __init__(self, framerate):
#         self.framerate = framerate

#         pg.init()
#         self.display = pg.display.set_mode((800, 400))
#         self.clock = pg.time.Clock()

#     def run(self):
#         while True:
#             pg.display.update()
#             self.clock.tick(self.framerate)


# def main():
#     controller = GameController(5)
#     controller.run()


# if __name__ == "__main__":
#     main()
