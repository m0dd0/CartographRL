import numpy as np

from .terrains import Terrain


class Map:
    @classmethod
    def generate_A(cls):
        return cls(
            size=11,
            ruin_coords=[(1, 5), (2, 1), (2, 9), (8, 1), (8, 9), (9, 5)],
            mountain_coords=[(1, 3), (2, 8), (5, 5), (8, 2), (9, 7)],
            waste_coords=[],
        )

    @classmethod
    def generate_B(cls):
        raise NotImplementedError()

    @classmethod
    def generate_C(cls):
        raise NotImplementedError()

    @classmethod
    def generate_D(cls):
        raise NotImplementedError()

    @classmethod
    def generate_random(cls, n_ruins, n_mountains, n_wastes, seed):
        raise NotImplementedError()

    def __init__(self, size, ruin_coords, mountain_coords, waste_coords):
        self.terrain_map = np.full((size, size), Terrain.EMPTY)

        for mountain_coord in mountain_coords:
            self.terrain_map[mountain_coord] = Terrain.MOUNTAIN.value
        for waste_coord in waste_coords:
            self.terrain_map[waste_coord] = Terrain.WASTE.value

        # ruins are not a terrain, but a special case
        self.ruin_coords = ruin_coords

    def set_field(self, exploration_option, rotation, position):
        
