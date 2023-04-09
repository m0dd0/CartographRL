""" Representation of the game map. """

from typing import List, Tuple, Iterator

import numpy as np
import skimage as ski
from nptyping import NDArray, Shape, Int, Bool

from .general import InvalidMoveError, Terrains


class Map:
    @classmethod
    def generate_A(cls):
        return cls(
            size=11,
            ruin_coords=np.array(
                [(1, 5), (2, 1), (2, 9), (8, 1), (8, 9), (9, 5)], dtype=int
            ),
            mountain_coords=np.array(
                [(1, 3), (2, 8), (5, 5), (8, 2), (9, 7)], dtype=int
            ),
            waste_coords=np.array([], dtype=int),
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
        ruin_coords: NDArray[Shape["Nr, 2"], Int],
        mountain_coords: NDArray[Shape["Nm, 2"], Int],
        waste_coords: NDArray[Shape["Nw, 2"], Int],
    ):
        """Initialize a new map.

        Args:
            size (int): The size of the square map.
            ruin_coords (NDArray[Shape["Nr, 2"], Int]): The coordinates of the ruins.
            mountain_coords (NDArray[Shape["Nm, 2"], Int]): The coordinates of the mountains.
            waste_coords (NDArray[Shape["Nw, 2"], Int]): The coordinates of the wastelands.
        """
        self.size = size
        self.terrain_map = np.full((size, size), Terrains.EMPTY.value)

        for mountain_coord in mountain_coords:
            self.terrain_map[mountain_coord] = Terrains.MOUNTAIN.value
        for waste_coord in waste_coords:
            self.terrain_map[waste_coord] = Terrains.WASTE.value

        # ruins are not a terrain, but a special case
        self.ruin_coords = ruin_coords

    def _transform_to_map_coords(
        self,
        shape_coords: NDArray[Shape["N, 2"], Int],
        rotation: int,
        position: NDArray[Shape["2"], Int],
        mirror: bool,
    ) -> NDArray[Shape["N, 2"], Int]:
        """Transforms the coordinates of a piece to the map coordinates depending on the rotation and the position.
        Does not check if the transformed coordinates are valid.

        Args:
            shape_coords (NDArray[Shape["N, 2"], Int]): The coordinates of the piece, i.e. its shape. (NOT the map coordinates)
            rotation (int): The rotation of the piece in mulitples of 90 degrees. (1=90deg, 2=180deg, ...)
            position (NDArray[Shape["2"], Int]): The position of the piece.
            mirror (bool): Whether the piece is mirrored.

        Returns:
            NDArray[Shape["N, 2"], Int]: The transformed coordinates.
        """
        if mirror:
            shape_coords = np.array([(-x, y) for x, y in shape_coords])

        if rotation == 0:
            shape_coords = np.array(shape_coords)
        elif rotation == 1:
            shape_coords = np.array([(y, -x) for x, y in shape_coords])
        elif rotation == 2:
            shape_coords = np.array([(-x, -y) for x, y in shape_coords])
        elif rotation == 3:
            shape_coords = np.array([(-y, x) for x, y in shape_coords])
        else:
            raise ValueError(f"Invalid rotation: {rotation}")

        shape_coords[:, 0] -= np.min(shape_coords[:, 0])
        shape_coords[:, 1] -= np.min(shape_coords[:, 1])

        shape_coords = shape_coords + position

        return shape_coords

    def _transform_to_cluster(
        self,
        shape_coords: NDArray[Shape["N, 2"], Int],
        rotation: int,
        position: Tuple[Int, Int],
        mirror: bool,
    ) -> "Cluster":
        """Same as transform_to_map_coords, but returns a Cluster object.

        Args:
            shape_coords (NDArray[Shape["N, 2"], Int]): The coordinates of the piece, i.e. its shape. (NOT the map coordinates)
            rotation (int): The rotation of the piece in mulitples of 90 degrees. (1=90deg, 2=180deg, ...)
            position (Tuple[Int, Int]): The position of the piece.
            mirror (bool): Whether the piece is mirrored.

        Returns:
            Cluster: The transformed coordinates as a cluster object.
        """
        cluster_coords = self._transform_to_map_coords(
            shape_coords, rotation, position, mirror
        )
        return Cluster(cluster_coords, self)

    def place(
        self,
        shape_coords: NDArray[Shape["N, 2"], Int],
        terrain: Terrains,
        rotation: int,
        position: NDArray[Shape["2"], Int],
        mirror: bool,
        on_ruin: bool,
    ):
        """Places a piece on the map. Validates the move.

        Args:
            coords (NDArray[Shape["N, 2"], Int]): The original coordinates of the piece,
                i.e. its shape. (NOT the map coordinates)
            terrain (Terrains): The terrain of the piece.
            rotation (int): The rotation of the piece in mulitples of 90 degrees. (1=90deg, 2=180deg, ...)
            position (NDArray[Shape["2"], Int]): The position of the piece.
            mirror (bool): Whether the piece is mirrored.
            on_ruin (bool): Whether the piece must be placed on a ruin.

        Raises:
            InvalidMoveError: If the piece cannot be placed on the map.
        """
        cluster = self._transform_to_cluster(shape_coords, rotation, position, mirror)
        cluster.is_valid(on_ruin)
        self.terrain_map[shape_coords] = terrain.value

    def is_setable(self, coords, rotation, position, mirror, on_ruin):
        """Checks if a piece can be placed on the map.

        Args:
            coords (NDArray[Shape["N, 2"], Int]): The original coordinates of the piece,
                i.e. its shape. (NOT the map coordinates)
            rotation (int): The rotation of the piece in mulitples of 90 degrees. (1=90deg, 2=180deg, ...)
            position (NDArray[Shape["2"], Int]): The position of the piece.
            mirror (bool): Whether the piece is mirrored.
            on_ruin (bool): Whether the piece must be placed on a ruin.

        Returns:
            bool: Whether the piece can be placed on the map.
        """
        cluster = self._transform_to_cluster(coords, rotation, position, mirror)
        return cluster.is_valid(on_ruin, raise_error=False)

    def setable_options(
        self, shape_coords: NDArray[Shape["N, 2"], Int], on_ruin: bool
    ) -> Iterator[
        Tuple[NDArray[Shape["N, 2"], Int], int, NDArray[Shape["2"], Int], bool]
    ]:
        """Returns all possible placements of a piece on the map.

        Args:
            coords (NDArray[Shape["N, 2"], Int]): The original coordinates of the piece,
                i.e. its shape. (NOT the map coordinates)
            on_ruin (bool): Whether the piece must be placed on a ruin.

        Yields:
            Tuple[NDArray[Shape["N, 2"], Int], int, NDArray[Shape["2"], Int], bool]: The possible placements. (shape_coords, rotation, position, mirror)
        """
        for x in range(self.terrain_map.shape[0]):
            for y in range(self.terrain_map.shape[1]):
                for r in range(4):
                    for mirror in [False, True]:
                        if self._transform_to_cluster(
                            shape_coords, r, (x, y), mirror
                        ).is_valid(on_ruin):
                            yield (shape_coords, r, (x, y), mirror)

    def is_setable_anywhere(
        self,
        coords: NDArray[Shape["N, 2"], Int],
        on_ruin: bool,
    ) -> bool:
        try:
            next(self.setable_options(coords, on_ruin))
            return True
        except StopIteration:
            return False

    def eval_monsters(self) -> int:
        """Gets the number of empty fields which are adjacent to a monster."""
        cluster = Cluster(np.argwhere(self.terrain_map == Terrains.MONSTER.value), self)
        return sum(t == Terrains.EMPTY for t in cluster.surrounding_terrains())

    def get_surrounded_mountains(self) -> int:
        """Returns the number of mountains that are fully surrounded.

        Returns:
            int: The number of mountains that are surrounded by other mountains.
        """
        coords = np.argwhere(self.terrain_map == Terrains.MOUNTAIN.value)
        return sum([Cluster(c, self).is_surrounded() for c in coords])

    def clusters(self, terrain_type: Terrains) -> List["Cluster"]:
        """Returns all clusters of a terrain type.

        Args:
            terrain_type (Terrains): The terrain type.

        Returns:
            List[Cluster]: The clusters.
        """
        cluster_map = ski.measure.label(
            self.terrain_map == terrain_type.value, background=False, connectivity=1
        )

        return [
            Cluster(np.argwhere(cluster_map == cluster_label), self)
            for cluster_label in np.unique(cluster_map)
            if cluster_label != 0
        ]

    def __getitem__(self, key):
        return self.terrain_map[key]


class Cluster:
    def __init__(self, coords: NDArray[Shape["N, 2"], Int], map_sheet: Map):
        """Representation of a cluster of coordinates in context of the map.
        Contains different methods to get information about the cluster.
        Does not modify the map at any operation.
        Intended to prevent overloading the map class with methods.

        Args:
            coords (NDArray[Shape["N, 2"], Int]): The coordinates.
            map_sheet (Map): The map sheet.
        """
        self.coords = coords
        self.map_sheet = map_sheet

    def surrounding_mask(self) -> NDArray[Shape["S, S"], Bool]:
        """Returns a mask of the surrounding area of the cluster.

        Returns:
            NDArray[Shape["S, S"], Bool]: The mask.
        """
        f = np.full(self.map_sheet.terrain_map.shape, False)
        f[self.coords] = True
        return ski.segmentation.find_boundaries(f, mode="outer", connectivity=1)

    def surrounding_coords(self) -> NDArray[Shape["N, 2"], Int]:
        """Returns the coordinates of the surrounding area of the cluster.

        Returns:
            NDArray[Shape["N, 2"], Int]: The coordinates.
        """
        return np.argwhere(self.surrounding_mask())

    def surrounding_map(self) -> NDArray[Shape["S, S"], Int]:
        """Returns the map of the surrounding area of the cluster.
        Fields which are not part of the surrounding area are set to -1.

        Returns:
            NDArray[Shape["S, S"], Int]: The surrounding map.
        """
        f = self.map_sheet.terrain_map.copy()
        f[not self.surrounding_mask()] = -1

        return f

    def surrounding_terrains(self) -> NDArray[Shape["N"], Int]:
        """Returns the terrains of the surrounding area of the cluster.

        Returns:
            NDArray[Shape["N"], Int]: The terrains.
        """
        return self.map_sheet.terrain_map[self.surrounding_coords()]

    def on_edge(self) -> bool:
        """Returns whether the cluster has at least one element which is on the edge of the map.

        Returns:
            bool: Whether the cluster is on the edge.
        """
        return any(
            c in (0, self.map_sheet.terrain_map.shape[0] - 1)
            for c in self.coords.flatten()
        )

    def on_map(self) -> bool:
        """Returns whether the cluster is completely on the map, i.e. valid coordinates.

        Returns:
            bool: Whether the cluster is outside.
        """
        return all(
            coord[0] < 0
            or coord[0] >= self.terrain_map.shape[0]
            or coord[1] < 0
            or coord[1] >= self.terrain_map.shape[1]
            for coord in self.coords
        )

    def on_ruin(self) -> bool:
        """Returns  whehther at least one of the fields of the cluster is on a ruin.

        Returns:
            bool: Whether the cluster is on a ruin.
        """
        return any(c in self.map.ruin_coords for c in self.coords)

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
            self.map_sheet.terrain_map[coord] != Terrains.EMPTY.value
            for coord in self.coords
        )

    def is_valid(self, on_ruin: bool, raise_error: bool = False) -> bool:
        """Validates the cluster, i.e. checks whether it is on the map, not occupied and on a ruin if required.

        Args:
            on_ruin (bool): Whether the cluster must be on a ruin.
            raise_error (bool, optional): Whether to raise an error if the cluster is invalid. Defaults to False.

        Raises:
            InvalidMoveError: If the cluster is invalid and raise_error is True.

        Returns:
            bool: Whether the cluster is valid.
        """
        if not self.on_map():
            if raise_error:
                raise InvalidMoveError("At least one of the fields is out of bounds.")
            return False

        if self.is_occupied():
            if raise_error:
                raise InvalidMoveError("At least one of the fields is not empty.")
            return False

        if on_ruin and not self.on_ruin():
            if raise_error:
                raise InvalidMoveError("At least one of the fields must be on a ruin.")
            return False

        return True

    def __len__(self):
        return len(self.coords)
