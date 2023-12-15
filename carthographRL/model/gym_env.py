from gym import Env

from .model.carthographer_model_base import CarthographerModelBase


class CarthographersEnv(Env):
    metadata = {"render.modes": ["human"]}

    def __init__(self, implementation: CarthographerModelBase):
        self.implementation = implementation

        pass
