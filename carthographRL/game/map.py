from typing import List, Tuple

import numpy as np
import skimage as ski
from nptyping import NDArray, Shape, Int

from .general import InvalidMoveError, Terrains
from .exploration import ExplorationOption


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
    def generate_random(
        cls,
        n_ruins: int = 5,
        n_mountains: int = 5,
        n_wastes: int = 0,
        rng: np.random.Generator = None,
    ):
        raise NotImplementedError()

    def __init__(
        self,
        size: int,
        ruin_coords: List[Tuple[int, int]],
        mountain_coords: List[Tuple[int, int]],
        waste_coords: List[Tuple[int, int]],
    ):
        self.terrain_map = np.full((size, size), Terrains.EMPTY)

        for mountain_coord in mountain_coords:
            self.terrain_map[mountain_coord] = Terrains.MOUNTAIN.value
        for waste_coord in waste_coords:
            self.terrain_map[waste_coord] = Terrains.WASTE.value

        # ruins are not a terrain, but a special case
        self.ruin_coords = np.array(ruin_coords)

    def _validate_coords(
        self, coords: NDArray[Shape["N, 2"], Int], on_ruin: bool
    ) -> bool:
        if not np.all(coords < self.terrain_map.shape):
            raise InvalidMoveError("At least one of the fields is out of bounds.")

        if not np.all(self.terrain_map[coords] == Terrains.EMPTY.value):
            raise InvalidMoveError("At least one of the fields is not empty.")

        if on_ruin and len(
            set([tuple(c) for c in self.ruin_coords]).intersection(
                set([tuple(c) for c in coords])
            )
            == 0
        ):
            raise InvalidMoveError("At least one of the fields must be on a ruin.")

        return True

    def _transform_to_map_coords(
        self,
        coords: NDArray[Shape["N, 2"], Int],
        rotation: int,
        position: NDArray[Shape["2"], Int],
    ) -> NDArray[Shape["N, 2"], Int]:
        if rotation == 0:
            coords = np.array(coords)
        elif rotation == 1:
            coords = np.array([(y, -x) for x, y in coords])
        elif rotation == 2:
            coords = np.array([(-x, -y) for x, y in coords])
        elif rotation == 3:
            coords = np.array([(-y, x) for x, y in coords])
        else:
            raise ValueError(f"Invalid rotation: {rotation}")

        coords[:, 0] -= np.min(coords[:, 0])
        coords[:, 1] -= np.min(coords[:, 1])

        coords = coords + position

        return coords

    def get_surrounded_mountains(self) -> int:
        coords = np.argwhere(self.terrain_map == Terrains.MOUNTAIN.value)

        n_surrounded = 0
        for mountain_coord in coords:
            f = np.full(self.terrain_map.shape, 0)
            f[mountain_coord] = 1
            surrounding_terrains = self.terrain_map[
                np.argwhere(
                    ski.segmentation.find_boundaries(f, connectivity=1, mode="outer")
                )
            ]

            if np.all(surrounding_terrains != Terrains.EMPTY.value):
                n_surrounded += 1

        return n_surrounded

    def place(
        self,
        exploration_option: ExplorationOption,
        rotation: int,
        position: Tuple[int, int],
        on_ruin: bool,
    ):
        coords = self._transform_to_map_coords(
            np.array(exploration_option.coords), rotation, np.array(position)
        )
        self._validate_coords(coords, on_ruin)
        self.terrain_map[coords] = exploration_option.terrain.value

    def eval_monsters(self) -> int:
        monsters_boundary = ski.segmentation.find_boundaries(
            self.terrain_map == Terrains.MONSTER.value, connectivity=1, mode="outer"
        )

        return np.count_nonzero(monsters_boundary)

    def is_setable(self, exploration_option: ExplorationOption, on_ruin: bool) -> bool:
        for x in range(self.terrain_map.shape[0]):
            for y in range(self.terrain_map.shape[1]):
                for r in range(4):
                    try:
                        coords = self._transform_to_map_coords(
                            np.array(exploration_option.coords), r, np.array((x, y))
                        )
                        self._validate_coords(coords, on_ruin)
                        return True
                    except InvalidMoveError:
                        pass
        return False
