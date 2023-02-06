from enum import Enum
from itertools import groupby
from typing import List, Callable
from dataclasses import dataclass

import numpy as np
import skimage as ski
from nptype import NDArray, Shape, Int, Boole

from .general import Terrains, Card
from .map import Map


class TaskType(Enum):
    VILLAGE = 1
    WATER_FARM = 2
    FOREST = 3
    GEOMETRY = 4


@dataclass
class ScoringCard(Card):
    name: str
    card_id: int
    task_type: TaskType
    evaluate: Callable
    solo_points: int
    description: str


def _cluster_map(
    terrain_map: NDArray[Shape["S, S"], Int], terrain_type: int
) -> NDArray[Shape["S, S"], Int]:
    return ski.measure.label(
        terrain_map == terrain_type, background=False, connectivity=1
    )


def _clusters_masks(
    terrain_map: NDArray[Shape["S, S"], Int], terrain_type: int
) -> List[NDArray[Shape["S, S"], Boole]]:
    clusters = _cluster_map(terrain_map, terrain_type)
    clusters_maps = []
    for cluster_label in np.unique(clusters):
        if cluster_label == 0:
            continue

        clusters_maps.append(clusters == cluster_label)

    return clusters_maps


def _clusters_coords(
    terrain_map: NDArray[Shape["S, S"], Int], terrain_type: int
) -> List[NDArray[Shape["N, 2"], Int]]:
    clusters = _cluster_map(terrain_map, terrain_type)
    cluster_coords = []
    for cluster_label in np.unique(clusters):
        if cluster_label == 0:
            continue

        cluster_coords.append(np.argwhere(clusters == cluster_label))

    # cluster_coords = np.array(cluster_coords) # not possible as the cluster_coords have different lengths

    return cluster_coords


def _boundary_mask(
    terrain_map: NDArray[Shape["S, S"], Int], terrain_type: int
) -> NDArray[Shape["S, S"], Int]:
    return ski.segmentation.find_boundaries(
        terrain_map == terrain_type, mode="outer", connectivity=1
    )


def _boundaries_masks(
    terrain_map: NDArray[Shape["S, S"], Int], terrain_type: int
) -> List[NDArray[Shape["S, S"], Boole]]:
    cluster_masks = _clusters_masks(terrain_map, terrain_type)

    boundaries_masks = []
    for cluster_mask in cluster_masks:
        boundaries_masks.append(
            ski.segmentation.find_boundaries(cluster_mask, mode="outer", connectivity=1)
        )

    return boundaries_masks


def _boundaries_values(
    terrain_map: NDArray[Shape["S, S"], Int], terrain_type: int
) -> List[NDArray[Shape["N"], Int]]:
    boundaries_mask = _boundaries_masks(terrain_map, terrain_type)

    boundary_values = []
    for boundary_mask in boundaries_mask:
        boundary_values.append(terrain_map[boundary_mask])
    return boundary_values


def _boundaries_coords(
    terrain_map: NDArray[Shape["S, S"], Int], terrain_type: int
) -> List[NDArray[Shape["N, 2"], Int]]:
    boundaries_mask = _boundaries_masks(terrain_map, terrain_type)

    boundary_coords = []
    for boundary_mask in boundaries_mask:
        boundary_coords.append(np.argwhere(boundary_mask))

    return boundary_coords


def bastionen_der_wildnis(map_sheet: Map) -> int:
    """8 Punkte für jedes Dorf-Gebite das aus minedstens 6 Dorf-Feldern besteht."""
    cluster_coords = _clusters_coords(map_sheet.terrain_map, Terrains.VILLAGE.value)

    return len([c for c in cluster_coords if len(c) >= 6]) * 8


def metropole(map_sheet: Map) -> int:
    """1 Ruhmpunkt für jedes Dorf-Feld in deinem größten Dorf-Gebiet, das nicht an ein oder mehrere Gebirgs-Felder angrenzt."""

    clusters_coords = _clusters_coords(map_sheet.terrain_map, Terrains.VILLAGE.value)

    valid_cluster_sizes = []
    for cluster_coords in clusters_coords:
        if Terrains.MOUNTAIN.value not in map_sheet.terrain_map[cluster_coords]:
            valid_cluster_sizes.append(len(cluster_coords))

    return max(valid_cluster_sizes) if valid_cluster_sizes else 0


def schild_des_reiches(map_sheet: Map) -> int:
    """2 Ruhmpunkte für jedes Dorf-Feld in deinem zweitgrößten Dorf-Gebiet."""
    clusters = _cluster_map(map_sheet.terrain_map, Terrains.VILLAGE.value)
    cluster_labels, cluster_sizes = np.unique(clusters, return_counts=True)

    if len(cluster_labels) < 3:
        # there is only one or no house cluster so there is no second largest cluster
        return 0

    return np.sort(cluster_sizes)[-2] * 2


def schillernde_ebene(map_sheet: Map) -> int:
    """3 Ruhmpunkte für jedes Dorf-Gebiet das an mindestens 3 unterschieldiche Geländearten angrenzt."""

    boundarys_values = _boundary_values_by_cluster(
        map_sheet.terrain_map, Terrains.VILLAGE.value
    )
    score = 0
    for boundary_values in boundarys_values:
        boundary_values = list(np.unique(boundary_values))
        boundary_values.remove(Terrains.EMPTY.value)
        if len(boundary_values) >= 3:
            score += 3

    return score


def karawanserei(map_sheet: Map) -> int:
    """1 Ruhmpunkt für jede Zeile und Spalte mit mindestens 1 Feld eines von dir gewählten Dorf-Gebietes."""

    clusters_coords = _cluster_coords(map_sheet.terrain_map, Terrains.VILLAGE.value)

    scores = []
    for cluster_coords in clusters_coords:
        n_rows = np.max(cluster_coords[:, 0]) - np.min(cluster_coords[:, 0]) + 1
        n_cols = np.max(cluster_coords[:, 1]) - np.min(cluster_coords[:, 1]) + 1

        scores.append(n_rows + n_cols)

    return max(scores) if scores else 0


def die_aeusserste_enklave(map_sheet: Map) -> int:
    """1 Ruhmpunkt für jedes leere Feld, das an ein von dir gewähltes Dorf-Gebiet angrenzt."""

    boundaries_values = _boundary_values_by_cluster(
        map_sheet.terrain_map, Terrains.VILLAGE.value
    )

    scores = []
    for boundary_values in boundaries_values:
        scores.append(len(boundary_values[boundary_values == Terrains.EMPTY.value]))

    return max(scores) if scores else 0


def gnomkolonie(map_sheet: Map) -> int:
    """6 Ruhmpunkte für jedes Dorf-Gebite mit mindestens 1 ausgefüllten Quadrat der größe 2x2."""

    clusters_coords = _cluster_coords(map_sheet.terrain_map, Terrains.VILLAGE.value)

    score = 0
    for cluster_coords in clusters_coords:
        for cluster_coord in cluster_coords:
            needed_coords = set(
                [
                    tuple(cluster_coord),
                    tuple(cluster_coord + np.array([0, 1])),
                    tuple(cluster_coord + np.array([1, 0])),
                    tuple(cluster_coord + np.array([1, 1])),
                ]
            )
            if needed_coords <= set([tuple(idx) for idx in cluster_coords]):
                score += 6
                break

    return score


def traykloster(map_sheet: Map) -> int:
    """7 Ruhmpunkte für jedes Dorf-Gebiet mit mindestens 1 ausgefüllten Rechteck der größe 1x4 (oder 4x1)."""

    clusters_coords = _cluster_coords(map_sheet.terrain_map, Terrains.VILLAGE.value)

    score = 0
    for cluster_coords in clusters_coords:
        c_map = np.zeros(map_sheet.terrain_map.shape, dtype=bool)
        c_map[cluster_coords] = True

        for line in c_map.tolist() + c_map.T.tolist():
            house_counts = [
                sum(1 for _ in group) for val, group in groupby(line) if val
            ]
            n_houses = max(house_counts) if len(house_counts) > 0 else 0
            if n_houses >= 4:
                score += 7
                break

    return score


def pfad_des_waldes(map_sheet: Map) -> int:
    """3 Ruhmpunkte für jedes Gebirgs-Feld, das über mindestens 1 Wald-Gebiet mit mindestens 1 anderen Gebirgs-Feld verbunden ist."""

    boundaries_values = _boundary_values_by_cluster(
        map_sheet.terrain_map, Terrains.FOREST.value
    )

    valid_mountains = set()
    for boundary_values in boundaries_values:
        if np.sum(boundary_values == Terrains.MOUNTAIN.value) >= 2:
            valid_mountains.update(
                set(
                    [
                        tuple(idx)
                        for idx in np.argwhere(
                            boundary_values == Terrains.MOUNTAIN.value
                        )
                    ]
                )
            )

    # clusters = ski.measure.label(
    #     map_sheet == Terrains.FOREST.value, background=False, connectivity=1
    # )

    # bonus_mountains_indices = set()
    # for cluster_label in np.unique(clusters):
    #     if cluster_label == 0:
    #         continue

    #     surrounding_mask = ski.segmentation.find_boundaries(
    #         clusters == cluster_label, mode="outer", connectivity=1
    #     )

    #     connected_mountains_indices = np.argwhere(
    #         np.logical_and(surrounding_mask, map_sheet == Terrains.MOUNTAIN.value)
    #     )
    #     if len(connected_mountains_indices) > 1:
    #         bonus_mountains_indices.update(
    #             set([tuple(idx) for idx in connected_mountains_indices])
    #         )

    # return len(bonus_mountains_indices) * 3


def schildwald(map_sheet: Map) -> int:
    """1 Ruhmpunkt für jedes Wald-Feld das an den Rand grenzt."""

    edge = np.concatenate(
        (map_sheet[0, :], map_sheet[-1, :], map_sheet[1:-1, 0], map_sheet[1:-1, -1])
    )

    return np.count_nonzero(edge == Terrains.FOREST.value)


def gruenflaeche(map_sheet: Map) -> int:
    """1 Ruhmpunkt für jede Zeile und Spalte mit mindestens 1 Wald-Feld."""

    n_lines = 0

    for row in map_sheet:
        if Terrains.FOREST.value in row:
            n_lines += 1

    for col in map_sheet.T:
        if Terrains.FOREST.value in col:
            n_lines += 1

    return n_lines


def duesterwald(map_sheet: Map) -> int:
    """1 Ruhmpunkt für jedes Wald-Feld das an 4 ausgefüllte Felder (und/oder den Rand) angrenzt."""

    score = 0

    for forest_idx in np.argwhere(map_sheet == Terrains.FOREST.value):
        f = np.full(map_sheet.shape, 0)
        f[forest_idx[0], forest_idx[1]] = 1
        surrounding_mask = ski.segmentation.find_boundaries(
            f, mode="outer", connectivity=1
        )

        if Terrains.EMPTY.value not in map_sheet[np.argwhere(surrounding_mask)]:
            score += 1

    return score


def goldener_kornspeicher(map_sheet: Map) -> int:
    """1 Ruhmpunkt für jedes Wasser-Feld, das an minestens 1 Ruinen-Feld grenzt. 3 Ruhmpunkte für jedes Acker-Feld, auf einem Ruinen-Feld."""

    # TODO this is the only scoring card in cartographers that uses the tempel map_sheet
    # we need to implement the handling of the tempel map_sheet first
    raise NotImplementedError()


def tal_der_magier(map_sheet: Map) -> int:
    """2 Ruhmpunkte für jedes Wasser-Feld, das an mindestens 1 Gebirgs-Feld grenzt. 1 Ruhmpunkt für jedes Acker-Feld, das an mindestens 1 Gebirgs-Feld grenzt."""

    score = 0

    for water_idx in np.argwhere(map_sheet == Terrains.WATER.value):
        f = np.full(map_sheet.shape, 0)
        f[water_idx[0], water_idx[1]] = 1
        surrounding_mask = ski.segmentation.find_boundaries(
            f, mode="outer", connectivity=1
        )

        if Terrains.MOUNTAIN.value in map_sheet[np.argwhere(surrounding_mask)]:
            score += 2

    for map_sheet_idx in np.argwhere(map_sheet == Terrains.FARM.value):
        f = np.full(map_sheet.shape, 0)
        f[map_sheet_idx[0], map_sheet_idx[1]] = 1
        surrounding_mask = ski.segmentation.find_boundaries(
            f, mode="outer", connectivity=1
        )

        if Terrains.MOUNTAIN.value in map_sheet[np.argwhere(surrounding_mask)]:
            score += 1

    return score


def bewaesserungskanal(map_sheet: Map) -> int:
    """1 Ruhmpunkt für jedes Wasser-Feld, das an mindestens 1 Acker-Feld grenzt. 1 Ruhmpunkt für jedes Acker-Feld, das an mindestens 1 Wasser-Feld grenzt."""

    score = 0

    for water_idx in np.argwhere(map_sheet == Terrains.WATER.value):
        f = np.full(map_sheet.shape, 0)
        f[water_idx[0], water_idx[1]] = 1
        surrounding_mask = ski.segmentation.find_boundaries(
            f, mode="outer", connectivity=1
        )

        if Terrains.FARM.value in map_sheet[np.argwhere(surrounding_mask)]:
            score += 1

    for map_sheet_idx in np.argwhere(map_sheet == Terrains.FARM.value):
        f = np.full(map_sheet.shape, 0)
        f[map_sheet_idx[0], map_sheet_idx[1]] = 1
        surrounding_mask = ski.segmentation.find_boundaries(
            f, mode="outer", connectivity=1
        )

        if Terrains.WATER.value in map_sheet[np.argwhere(surrounding_mask)]:
            score += 1

    return score


def ausgedehnte_straende(map_sheet: Map) -> int:
    """3 Ruhmpunkte für für jedes Acker-Gebiet, das weder an den Rand noch an 1 oder mehrere Wasser-Felder grenzt. 3 Ruhmpunkte für jedes Wasser-Gebiet, das weder an den Rand noch an 1 oder mehrere Acker-Felder grenzt."""

    score = 0
    for space_type_1, space_type_2 in [
        (Terrains.FARM.value, Terrains.WATER.value),
        (Terrains.WATER.value, Terrains.FARM.value),
    ]:
        clusters = ski.measure.label(
            map_sheet == space_type_1, background=False, connectivity=1
        )
        for cluster_label in np.unique(clusters):
            if cluster_label == 0:
                continue

            cluster = clusters == cluster_label
            cluster_indices = np.argwhere(cluster)
            surrounding_mask = ski.segmentation.find_boundaries(
                cluster, mode="outer", connectivity=1
            )
            surrounding_indices = np.argwhere(surrounding_mask)

            if space_type_2 not in map_sheet[surrounding_indices] and np.all(
                cluster_indices[:, 0] > 0
                and cluster_indices[:, 0] < map_sheet.shape[0] - 1
                and cluster_indices[:, 1] > 0
                and cluster_indices[:, 1] < map_sheet.shape[1] - 1
            ):
                score += 3

    return score


SCORING_CARDS = [
    ScoringCard(
        "Bastionen in der Wildnis",
        134,
        TaskType.VILLAGE,
        bastionen_der_wildnis,
        16,
        "8 Punkte für jedes Dorf-Gebite das aus minedstens 6 Dorf-Feldern besteht.",
    ),
    ScoringCard(
        "Metropole",
        135,
        TaskType.VILLAGE,
        metropole,
        16,
        "1 Ruhmpunkt für jedes Dorf-Feld in deinem größten Dorf-Gebiet, das nicht an ein oder mehrere Gebirgs-Felder angrenzt.",
    ),
    ScoringCard(
        "Schild des Reiches",
        137,
        TaskType.VILLAGE,
        schild_des_reiches,
        20,
        "2 Ruhmpunkte für jedes Dorf-Feld in deinem zweitgrößten Dorf-Gebiet.",
    ),
    ScoringCard(
        "Schillernde Ebene",
        136,
        TaskType.VILLAGE,
        schillernde_ebene,
        21,
        "3 Ruhmpunkte für jedes Dorf-Gebiet das an mindestens 3 unterschieldiche Geländearten angrenzt.",
    ),
    ScoringCard(
        "Karawanserei",
        239,
        TaskType.VILLAGE,
        karawanserei,
        16,
        "1 Ruhmpunkt für jede Zeile und Spalte mit mindestens 1 Feld eines von dir gewählten Dorf-Gebietes.",
    ),
    ScoringCard(
        "Die äußerste Enklave",
        237,
        TaskType.VILLAGE,
        die_aeusserste_enklave,
        12,
        "1 Ruhmpunkt für jedes leere Feld, das an ein von dir gewähltes Dorf-Gebiet angrenzt.",
    ),
    ScoringCard(
        "Gnomkolonie",
        238,
        TaskType.VILLAGE,
        gnomkolonie,
        12,
        "6 Ruhmpunkte für jedes Dorf-Gebite mit mindestens 1 ausgefüllten Quadrat der größe 2x2.",
    ),
    ScoringCard(
        "Traykloster",
        236,
        TaskType.VILLAGE,
        traykloster,
        14,
        "7 Ruhmpunkte für jedes Dorf-Gebiet mit mindestens 1 ausgefüllten Rechteck der größe 1x4 (oder 4x1).",
    ),
    ScoringCard(
        "Pfad des Waldes",
        129,
        TaskType.FOREST,
        pfad_des_waldes,
        18,
        "3 Ruhmpunkte für jedes Gebirgs-Feld, das über mindestens 1 Wald-Gebiet mit mindestens 1 anderen Gebirgs-Feld verbunden ist.",
    ),
    ScoringCard(
        "Schildwald",
        126,
        TaskType.FOREST,
        schildwald,
        25,
        "1 Ruhmpunkt für jedes Wald-Feld das an den Rand grenzt.",
    ),
    ScoringCard(
        "Grünfläche",
        127,
        TaskType.FOREST,
        gruenflaeche,
        22,
        "1 Ruhmpunkt für jede Zeile und Spalte mit mindestens 1 Wald-Feld.",
    ),
    ScoringCard(
        "Düsterwald",
        128,
        TaskType.FOREST,
        duesterwald,
        17,
        "1 Ruhmpunkt für jedes Wald-Feld das an 4 ausgefüllte Felder (und/oder den Rand) angrenzt.",
    ),
    ScoringCard(
        "Goldener Kornspeicher",
        132,
        TaskType.WATER_FARM,
        goldener_kornspeicher,
        20,
        "1 Ruhmpunkt für jedes Wasser-Feld, das an minestens 1 Ruinen-Feld grenzt. 3 Ruhmpunkte für jedes Acker-Feld, auf einem Ruinen-Feld.",
    ),
    ScoringCard(
        "Tal der Magier",
        131,
        TaskType.WATER_FARM,
        tal_der_magier,
        22,
        "2 Ruhmpunkte für jedes Wasser-Feld, das an mindestens 1 Gebirgs-Feld grenzt. 1 Ruhmpunkt für jedes Acker-Feld, das an mindestens 1 Gebirgs-Feld grenzt.",
    ),
    ScoringCard(
        "Bewässerungskanal",
        130,
        TaskType.WATER_FARM,
        bewaesserungskanal,
        24,
        "1 Ruhmpunkt für jedes Wasser-Feld, das an mindestens 1 Acker-Feld grenzt. 1 Ruhmpunkt für jedes Acker-Feld, das an mindestens 1 Wasser-Feld grenzt.",
    ),
    ScoringCard(
        "Ausgedehnte Strände",
        133,
        TaskType.WATER_FARM,
        ausgedehnte_straende,
        27,
        "3 Ruhmpunkte für für jedes Acker-Gebiet, das weder an den Rand noch an 1 oder mehrere Wasser-Felder grenzt. 3 Ruhmpunkte für jedes Wasser-Gebiet, das weder an den Rand noch an 1 oder mehrere Acker-Felder grenzt.",
    ),
]

SCORING_CARDS_BY_NAME = {c.name: c for c in SCORING_CARDS}
SCORING_CARDS_BY_ID = {c.id: c for c in SCORING_CARDS}


class ScoringDeck:
    def __init__(
        self,
        heroes: bool = False,
        rng: np.random.Generator = None,
        predefined_cards: List[ScoringCard] = None,
    ):
        assert not heroes, "Heroes not supported yet"

        self.predefined_cards = predefined_cards

        if rng is None:
            rng = np.random.default_rng()
        self.rng = rng

        self._all_cards = [c for c in SCORING_CARDS if heroes or not c.is_hero()]

        self._cards_by_type = {}
        for t in TaskType:
            cards = [c for c in self._all_cards if c.task_type == t]
            rng.shuffle(cards)
            self._cards_by_type[t] = cards

    def draw_scoring_card(
        self,
        order: List[TaskType],
    ) -> List[ScoringCard]:
        if self.predefined_cards is not None:
            return self.predefined_cards

        if order is None:
            order = self.rng.shuffle(
                [
                    TaskType.VILLAGE,
                    TaskType.FOREST,
                    TaskType.WATER_FARM,
                    TaskType.MOUNTAIN,
                ]
            )

        assert len(order) == len(set([t.value for t in order])) == 4

        scoring_card = [self.rng.choice(self._cards_by_type[t]) for t in order]

        return scoring_card
