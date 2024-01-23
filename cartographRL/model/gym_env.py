from gym import Env

from carthographRL.model.carthographer_model_base import CarthographerModelBase


class CarthographersEnv(Env):
    metadata = {"render.modes": ["human"]}

    def __init__(self, implementation: CarthographerModelBase):
        self.implementation = implementation

        pass
