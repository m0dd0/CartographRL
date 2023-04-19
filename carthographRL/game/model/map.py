""" Representation of the game map. """

from typing import List, Tuple, Iterable, FrozenSet

import numpy as np
import skimage as ski
from nptyping import NDArray, Shape, Int, Bool

from .general import InvalidMoveError, Terrains


class Map:
    @classmethod
    def generate_A(cls):
        return cls(
            size=11,
            ruin_coords=frozenset(
                [(1, 5), (2, 1), (2, 9), (8, 1), (8, 9), (9, 5)],
            ),
            mountain_coords=frozenset([(1, 3), (2, 8), (5, 5), (8, 2), (9, 7)]),
            waste_coords=frozenset([]),
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
        ruin_coords: FrozenSet[Tuple[int, int]],
        mountain_coords: FrozenSet[Tuple[int, int]],
        waste_coords: FrozenSet[Tuple[int, int]],
    ):
        """Initialize a new map.

        Args:
            size (int): The size of the square map.
            ruin_coords (FrozenSet[Tuple[int, int]]): The coordinates of the ruins.
            mountain_coords (FrozenSet[Tuple[int, int]]): The coordinates of the mountains.
            waste_coords (FrozenSet[Tuple[int, int]]): The coordinates of the wastelands.
        """
        self.size = size
        self.terrain_map = np.full((size, size), Terrains.EMPTY.value)

        for mountain_coord in mountain_coords:
            self.terrain_map[
                mountain_coord[0], mountain_coord[1]
            ] = Terrains.MOUNTAIN.value
        for waste_coord in waste_coords:
            self.terrain_map[waste_coord[0], waste_coord[1]] = Terrains.WASTE.value

        # ruins are not a terrain, but a special case
        self.ruin_coords = ruin_coords

        self._all_action_tuples = [
            (x, y, r, m)
            for x in range(self.terrain_map.shape[0])
            for y in range(self.terrain_map.shape[1])
            for r in range(4)
            for m in [False, True]
        ]

    def transform_to_map_coords(
        self,
        shape_coords: FrozenSet[Tuple[int, int]],
        rotation: int,
        position: FrozenSet[Tuple[int, int]],
        mirror: bool,
    ) -> FrozenSet[Tuple[int, int]]:
        """Transforms the coordinates of a piece to the map coordinates depending on the rotation and the position.
        Does not check if the transformed coordinates are valid.

        Args:
            shape_coords ( FrozenSet[Tuple[int, int]]): The coordinates of the piece, i.e. its shape. (NOT the map coordinates)
            rotation (int): The rotation of the piece in mulitples of 90 degrees. (1=90deg, 2=180deg, ...)
            position (Tuple[int, int]): The position of the piece.
            mirror (bool): Whether the piece is mirrored.

        Returns:
             FrozenSet[Tuple[int, int]]: The transformed coordinates.
        """
        if mirror:
            shape_coords = {(-x, y) for x, y in shape_coords}

        if rotation == 0:
            shape_coords = shape_coords
        elif rotation == 1:
            shape_coords = {(y, -x) for x, y in shape_coords}
        elif rotation == 2:
            shape_coords = {(-x, -y) for x, y in shape_coords}
        elif rotation == 3:
            shape_coords = {(-y, x) for x, y in shape_coords}
        else:
            raise ValueError(f"Invalid rotation: {rotation}")

        min_x = min(x for x, _ in shape_coords)
        min_y = min(y for _, y in shape_coords)
        shape_coords = {(x - min_x, y - min_y) for x, y in shape_coords}

        shape_coords = {(x + position[0], y + position[1]) for x, y in shape_coords}

        return frozenset(shape_coords)

    def place(
        self, map_coords: FrozenSet[Tuple[int, int]], terrain: Terrains, on_ruin: bool
    ):
        """Places a piece on the map. Validates the move.

        Args:
            coords (FrozenSet[Tuple[int, int]]): The map coordinates of all fields of the piece.
            terrain (Terrains): The terrain of the piece.
            on_ruin (bool): Whether the piece must be placed on a ruin.

        Raises:
            InvalidMoveError: If the piece cannot be placed on the map.
        """
        if not self.is_setable(map_coords, on_ruin):
            raise InvalidMoveError("Invalid move.")
        x_idx, y_idx = zip(*map_coords)
        self.terrain_map[x_idx, y_idx] = terrain.value

    def is_setable(self, map_coords: FrozenSet[Tuple[int, int]], on_ruin: bool) -> bool:
        """Checks if an intended move is valid.

        Args:
            coords (FrozenSet[Tuple[int, int]]): The map coordinates of all fields of the piece.
            on_ruin (bool): Whether the piece must be placed on a ruin.

        Returns:
            bool: Whether the move is valid.
        """
        return Cluster(map_coords, self).is_valid(on_ruin)

    def setable_map_coords(
        self, shape_coords, on_ruin: bool
    ) -> Iterable[FrozenSet[Tuple[int, int]]]:
        """Generates all possible map coordinates sets for a piece.

        Args:
            coords (FrozenSet[Tuple[int, int]]): The original coordinates of the piece,
                i.e. its shape. (NOT the map coordinates)
            on_ruin (bool): Whether the piece must be placed on a ruin.

        Yields:
            Iterable[FrozenSet[Tuple[int, int]]]: All possible map coordinates sets for a piece.
        """

        for x, y, r, m in self._all_action_tuples:
            map_coords = self.transform_to_map_coords(shape_coords, r, (x, y), m)
            if self.is_setable(map_coords, on_ruin):
                yield map_coords

    def is_setable_anywhere(
        self, coords: FrozenSet[Tuple[int, int]], on_ruin: bool
    ) -> bool:
        """Checks if a piece can be placed anywhere on the map.

        Args:
            coords (FrozenSet[Tuple[int, int]]): The original coordinates of the piece,
                i.e. its shape. (NOT the map coordinates)
            on_ruin (bool): Whether the piece must be placed on a ruin.

        Returns:
            bool: Whether the piece can be placed anywhere on the map.
        """
        try:
            next(self.setable_map_coords(coords, on_ruin))
            return True
        except StopIteration:
            return False

    def eval_monsters(self) -> int:
        """Gets the number of empty fields which are adjacent to a monster."""
        cluster = Cluster(np.argwhere(self.terrain_map == Terrains.MONSTER.value), self)
        return sum(t == Terrains.EMPTY.value for t in cluster.surrounding_terrains())

    def get_surrounded_mountains(self) -> int:
        """Returns the number of mountains that are fully surrounded.

        Returns:
            int: The number of mountains that are surrounded by other mountains.
        """
        coords = np.argwhere(self.terrain_map == Terrains.MOUNTAIN.value)
        return sum([Cluster(c, self).is_surrounded() for c in coords])

    def clusters(self, terrain_type: Terrains) -> FrozenSet["Cluster"]:
        """Returns all clusters of a terrain type.

        Args:
            terrain_type (Terrains): The terrain type.

        Returns:
            FrozenSet[Cluster]: The clusters.
        """
        cluster_map = ski.measure.label(
            self.terrain_map == terrain_type.value, background=False, connectivity=1
        )

        return frozenset(
            {
                Cluster(np.argwhere(cluster_map == cluster_label), self)
                for cluster_label in np.unique(cluster_map)
                if cluster_label != 0
            }
        )

    def to_list(self) -> List[List[Terrains]]:
        """Returns a list representation of the map.

        Returns:
            List[List[Terrains]]: The list representation.
        """
        return [[Terrains(t) for t in row] for row in self.terrain_map]


class Cluster:
    def __init__(self, coords: FrozenSet[Tuple[int, int]], map_sheet: Map):
        """Representation of a cluster of coordinates in context of the map.
        Contains different methods to get information about the cluster.
        Does not modify the map at any operation.
        Intended to prevent overloading the map class with methods.

        Args:
            coords (FrozenSet[Tuple[int, int]]): The coordinates.
            map_sheet (Map): The map sheet.
        """
        self.coords = coords
        self._map_sheet = map_sheet

    def surrounding_mask(self) -> NDArray[Shape["S, S"], Bool]:
        """Returns a mask of the surrounding area of the cluster.

        Returns:
            NDArray[Shape["S, S"], Bool]: The mask.
        """
        f = np.full(self._map_sheet.terrain_map.shape, False)
        x_idx, y_idx = zip(*self.coords)
        f[x_idx, y_idx] = True
        return ski.segmentation.find_boundaries(f, mode="outer", connectivity=1)

    def surrounding_coords(self) -> FrozenSet[Tuple[int, int]]:
        """Returns the coordinates of the surrounding area of the cluster.

        Returns:
             FrozenSet[Tuple[int, int]]: The coordinates.
        """
        return np.argwhere(self.surrounding_mask())

    def surrounding_map(self) -> NDArray[Shape["S, S"], Int]:
        """Returns the map of the surrounding area of the cluster.
        Fields which are not part of the surrounding area are set to -1.

        Returns:
            NDArray[Shape["S, S"], Int]: The surrounding map.
        """
        f = self._map_sheet.terrain_map.copy()
        f[not self.surrounding_mask()] = -1

        return f

    def surrounding_terrains(self) -> List[int]:
        """Returns the terrains of the surrounding area of the cluster.

        Returns:
            List[int]: The terrains.
        """
        x_idx, y_idx = zip(*self.surrounding_coords())
        return self._map_sheet.terrain_map[x_idx, y_idx].tolist()

    def on_edge(self) -> bool:
        """Returns whether the cluster has at least one element which is on the edge of the map.

        Returns:
            bool: Whether the cluster is on the edge.
        """
        return any(
            c in (0, self._map_sheet.terrain_map.shape[0] - 1)
            for coord_tuple in self.coords
            for c in coord_tuple
        )

    def on_map(self) -> bool:
        """Returns whether the cluster is completely on the map, i.e. valid coordinates.

        Returns:
            bool: Whether the cluster is on map.
        """
        return all(
            0 <= coord[0] < self._map_sheet.terrain_map.shape[0]
            and 0 <= coord[1] < self._map_sheet.terrain_map.shape[1]
            for coord in self.coords
        )

    def on_ruin(self) -> bool:
        """Returns  whehther at least one of the fields of the cluster is on a ruin.

        Returns:
            bool: Whether the cluster is on a ruin.
        """
        # return any(c in self.map.ruin_coords for c in self.coords)
        return len(self.coords.intersection(self._map_sheet.ruin_coords)) > 0

    def is_surrounded(self) -> bool:
        """Returns whether the cluster is completely surrounded by other terrains or on the edge of the map.

        Returns:
            bool: Whether the cluster is surrounded.
        """
        return Terrains.EMPTY.value not in self.surrounding_terrains()

    def is_occupied(self) -> bool:
        """Returns whether at least one of the fields of the cluster is not empty, i.e. the cluster cant be placed there.

        Returns:
            bool: Whether the cluster is occupied.
        """
        return any(
            self._map_sheet.terrain_map[coord[0], coord[1]] != Terrains.EMPTY.value
            for coord in self.coords
        )

    def is_valid(self, on_ruin: bool) -> bool:
        """Validates the cluster, i.e. checks whether it is on the map, not occupied and on a ruin if required.

        Args:
            on_ruin (bool): Whether the cluster must be on a ruin.

        Returns:
            bool: Whether the cluster is valid.
        """
        return (
            self.on_map()
            and not self.is_occupied()
            and (self.on_ruin() if on_ruin else True)
        )

    def __len__(self):
        return len(self.coords)

    def __hash__(self) -> int:
        return self.coords.__hash__()
