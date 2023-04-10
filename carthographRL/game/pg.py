# import pygame as pg


class Controller:
    def __init__(self, model, view):
        self.model = model
        self.view = view

    def run(self):
        while not self.model.finished:
            current_input = self.view.get_input()
            if current_input is not None:
                self.model.play(current_input)
                self.view.render(self.model)
            # self.view.get_imput()
            # pg.display.update()


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
