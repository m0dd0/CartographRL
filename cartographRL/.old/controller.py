from .model import CarthographersGame
from .view.base import View


class Controller:
    def __init__(self, model: CarthographersGame, view: View):
        self.model = model
        self.view = view

    def run(self):
        while not self.view.closed:
            action = self.view.render(self.model)
            # action = self.view.get_action()
            if action is not None:
                self.model.play(*action)

        self.view.cleanup()
