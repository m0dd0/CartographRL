"""Contains subclasses of pygame.Surface that are used to draw the UI elements.
These subclasses always act as a alternate constructor for the pygame.Surface class
and do not provide any additional functionality or attributes."""

from typing import Tuple, FrozenSet, Dict, Any
from pathlib import Path

import pygame

from ..base import get_asset_path
from ...model.general import Terrains


class RectSurf(pygame.Surface):
    def __init__(
        self,
        size: Tuple[int, int],
        frame_color: Tuple[int, int, int],
        frame_width: int,
        infill_color: Tuple[int, int, int],
        rounding: int,
    ):
        """Create a surface with a rectangular frame and an optional infill.
        When using rounded corners the remaining background is transparent.

        Args:
            size (Tuple[int, int]): Size of the surface.
            frame_color (Tuple[int, int, int]): Color of the frame.
            frame_width (int, optional): Width of the frame. If negative no frame is drawn.
            infill_color (Tuple[int, int, int], optional): Color of the infill. If None only a frame is drawn.
            rounding (int, optional): Radius of the rounded corners.
        """
        assert frame_width != 0, "Frame width must not be 0."
        super().__init__(size, pygame.SRCALPHA)
        self.fill((0, 0, 0, 0))
        if infill_color is not None:
            pygame.draw.rect(
                self, infill_color, pygame.Rect(0, 0, size[0], size[1]), 0, rounding
            )
        pygame.draw.rect(
            self,
            frame_color,
            pygame.Rect(0, 0, size[0], size[1]),
            frame_width,
            rounding,
        )


class ImageSurf(pygame.Surface):
    def __init__(
        self,
        size: Tuple[int, int],
        image: Path,
    ):
        """Create a surface with an image.
        The backgound is transparent to account for (partially) transparent images.

        Args:
            size (Tuple[int, int]): Size of the surface.
            image (Path): Path to the image file.
        """
        super().__init__(size, pygame.SRCALPHA)
        self.fill((0, 0, 0, 0))
        self.image = pygame.transform.scale(
            pygame.image.load(image).convert_alpha(), size
        )
        self.blit(self.image, (0, 0))


class ImageRectSurf(pygame.Surface):
    def __init__(
        self,
        size: Tuple[int, int],
        backgound_color: Tuple[int, int, int],
        frame_color: Tuple[int, int, int],
        frame_width: int,
        frame_rounding: int,
        image: Path,
        image_size: Tuple[int, int],
        image_offset: Tuple[int, int],
        opacity: int,
    ):
        """Create a surface with a rectangular frame, an optional infill and an image.
        As for nearly all UI elements we draw an image on a rect background this acts as a wrapper for the RectSurf and ImageSurf classes.
        However, in general it should be preferred to use the RectSurf and ImageSurf classes directly as this is more declarative and easier to understand.

        Args:
            size (Tuple[int, int]): Size of the surface.
            backgound_color (Tuple[int, int, int]): Color of the infill.
            frame_color (Tuple[int, int, int]): Color of the frame.
            frame_width (int): Width of the frame.
            frame_rounding (int): Radius of the rounded corners.
            image (Path): Path to the image file.
            image_size (Tuple[int, int], optional): Size of the image. If None, the size of the surface is used.
            image_offset (Tuple[int, int], optional): Offset of the image.
        """
        super().__init__(size, pygame.SRCALPHA)
        self.fill((0, 0, 0, 0))
        self.blit(
            RectSurf(size, frame_color, frame_width, backgound_color, frame_rounding),
            (0, 0),
        )
        image_size = image_size or size
        if image is not None:
            self.blit(ImageSurf(image_size, image), image_offset)

        self.set_alpha(opacity)


class FieldSurf(ImageRectSurf):
    def __init__(
        self,
        terrain: Terrains,
        ruin: bool,
        field_style: Dict[str, Any],
    ) -> None:
        """Surface of a singel field in the map or option card.

        Args:
            terrain (Terrains): Terrain of the field.
            ruin (bool): Whether the field is a ruin.
            candidate (bool): Whether the field is a candidate for a move (opposed to already set field)
            style (Dict[str, Any]): Style dictionary. Must contain the following keys:
                - size (int): Size of the field in pixels.
                - colors (Dict[str, Tuple[int, int, int]]): Colors of the fields.
                - frame_color (Tuple[int, int, int]): Color of the frame.
                - frame_width (int): Width of the frame.
                - frame_rounding (int): Radius of the rounded corners.
                - images (Dict[str, str]): Paths to the images of the fields.
                - image_size (Tuple[int, int]): Size of the image.
                - image_offset (Tuple[int, int]): Offset of the image.
                - opacity (int): Opacity of the field.
                - ruin_overlay (str): Path to the image of the ruin overlay.
        """
        terrain = terrain.name.lower()
        super().__init__(
            (field_style["size"], field_style["size"]),
            field_style["colors"][terrain],
            field_style["frame_color"],
            field_style["frame_width"],
            field_style["frame_rounding"],
            get_asset_path(field_style["images"][terrain]),
            field_style["image_size"],
            field_style["image_offset"],
            field_style["opacity"],
        )
        if ruin:
            self.blit(
                ImageSurf(
                    field_style["image_size"],
                    get_asset_path(field_style["ruin_overlay"]),
                ),
                field_style["image_offset"],
            )


class AreaSurf(pygame.Surface):
    def __init__(
        self,
        shape_coords: FrozenSet[Tuple[int, int]],
        terrain: Terrains,
        frame_width: int,
        frame_color: Tuple[int, int, int],
        field_style: Dict[str, Any],
    ):
        """Surface of a singel area in the map or option card.

        Args:
            shape_coords (Frozenset[Tuple[int, int]]): List of coordinates of the area.
            terrain (Terrains): Terrain of the area. If None, only the frame is drawn.
            frame_width (int): Width of the frame.
            frame_color (Tuple[int, int, int]): Color of the frame.
            field_style: (Dict[str, Any]): Style dictionary for the fields.
        """
        super().__init__(
            (max(c[0] for c in shape_coords), max(c[1] for c in shape_coords)),
            pygame.SRCALPHA,
        )
        self.fill((0, 0, 0, 0))

        edges = set()
        for x, y in shape_coords:
            top_edge = ((x, y), (x + 1, y))
            bottom_edge = ((x, y + 1), (x + 1, y + 1))
            left_edge = ((x, y), (x, y + 1))
            right_edge = ((x + 1, y), (x + 1, y + 1))

            top = (x - 1, y)
            bottom = (x - 1, y)
            left = (x, y - 1)
            right = (x, y + 1)

            if top not in shape_coords:
                edges.add(top_edge)
            if bottom not in shape_coords:
                edges.add(bottom_edge)
            if left not in shape_coords:
                edges.add(left_edge)
            if right not in shape_coords:
                edges.add(right_edge)

        for edge in edges:
            pygame.draw.line(
                self,
                frame_color,
                (edge[0][0] * field_style["size"], edge[0][1] * field_style["size"]),
                (edge[1][0] * field_style["size"], edge[1][1] * field_style["size"]),
                frame_width,
            )

        if terrain is not None:
            for x, y in shape_coords:
                field_surf = FieldSurf(terrain, False, field_style)
                self.blit(
                    field_surf, (x * field_style["size"], y * field_style["size"])
                )

