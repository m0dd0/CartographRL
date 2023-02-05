from enum import Enum
from itertools import groupby

import numpy as np
import skimage as ski


class TaskType(Enum):
    HOUSE = 1
    SEA_FIELD = 2
    FOREST = 3
    SIZE = 4


class SpaceType(Enum):
    HOUSE = 1
    SEA = 2
    FOREST = 3
    FIELD = 4
    DEVIL = 5
    EMPTY = 6
    MOUNTAIN = 7
    WASTE = 8


class ScoringCard:
    def __init__(
        self,
        name,
        card_id,
        task_type,
        evaluation_function,
        solo_points,
        description="<no description>",
    ):
        self.name = name
        self.card_id = card_id
        self.task_type = task_type
        self.evaluation_function = evaluation_function
        self.solo_points = solo_points
        self.description = description

    def evaluate(self, field):
        return self.evaluation_function(field)

    def __repr__(self):
        return self.name


# class Field:
#     def __init__(self, n_rows: int = 11, n_cols: int = 11):
#         self.n_rows = n_rows
#         self.n_cols = n_cols
#         self._field = np.full((n_rows, n_cols), SpaceType.EMPTY.value, dtype=np.int8)


def bastionen_der_wildnis(field):
    connected_areas = ski.measure.label(
        field == SpaceType.HOUSE.value, background=False, connectivity=1
    )

    score = 0
    for area_label in np.unique(connected_areas):
        if area_label == 0:  #  background is labeled 0
            continue

        if np.sum(connected_areas == area_label) >= 6:
            score += 8

    return score


def metropole(field):
    connected_areas = ski.measure.label(
        field == SpaceType.HOUSE.value, background=False, connectivity=1
    )
    area_labels, area_sizes = np.unique(connected_areas, return_counts=True)

    area_sizes_sorted = np.sort(area_sizes)[::-1]
    area_lablels_sorted = area_labels[np.argsort(area_sizes)[::-1]]

    for area_label, area_size in zip(area_lablels_sorted, area_sizes_sorted):
        if area_label == 0:  #  background is labeled 0
            continue

        area = connected_areas == area_label
        surrounding_mask = ski.segmentation.find_boundaries(
            area, mode="thick", connectivity=1
        )
        if SpaceType.MOUNTAIN.value not in field[np.argwhere(surrounding_mask)]:
            return area_size

    return 0


def schild_des_reiches(field):
    connected_areas = ski.measure.label(
        field == SpaceType.HOUSE.value, background=False, connectivity=1
    )
    area_labels, area_sizes = np.unique(connected_areas, return_counts=True)

    if len(area_labels) < 3:
        # there is only one or no house area so there is no second largest area
        return 0

    return np.sort(area_sizes)[-2] * 2


def schillernde_ebene(field):
    connected_areas = ski.measure.label(
        field == SpaceType.HOUSE.value, background=False, connectivity=1
    )

    score = 0
    for area_label in np.unique(connected_areas):
        if area_label == 0:  #  background is labeled 0
            continue

        surrounding_mask = ski.segmentation.find_boundaries(
            connected_areas == area_label, mode="thick", connectivity=1
        )
        surrounding_types = list(np.unique(field[np.argwhere(surrounding_mask)]))
        surrounding_types.remove(SpaceType.EMPTY.value)
        if len(surrounding_types) >= 3:
            score += 3

    return score


def karawanserei(field):
    connected_areas = ski.measure.label(
        field == SpaceType.HOUSE.value, background=False, connectivity=1
    )

    scores = []
    for area_label in np.unique(connected_areas):
        if area_label == 0:  #  background is labeled 0
            continue

        area_indices = np.argwhere(connected_areas == area_label)
        n_rows = np.max(area_indices[:, 0]) - np.min(area_indices[:, 0]) + 1
        n_cols = np.max(area_indices[:, 1]) - np.min(area_indices[:, 1]) + 1

        scores.append(n_rows + n_cols)

    if len(scores) == 0:
        return 0

    return max(scores)


def die_aeusserste_enklave(field):
    connected_areas = ski.measure.label(
        field == SpaceType.HOUSE.value, background=False, connectivity=1
    )

    scores = []
    for area_label in np.unique(connected_areas):
        if area_label == 0:
            continue

        surrounding_mask = ski.segmentation.find_boundaries(
            connected_areas == area_label, mode="thick", connectivity=1
        )
        surrounding_spaces = field[np.argwhere(surrounding_mask)]
        scores.append(len(surrounding_spaces == SpaceType.EMPTY.value))

    if len(scores) == 0:
        return 0

    return max(scores)


def gnomkolonie(field):
    connected_areas = ski.measure.label(
        field == SpaceType.HOUSE.value, background=False, connectivity=1
    )

    score = 0
    for area_label in np.unique(connected_areas):
        if area_label == 0:
            continue

        area = connected_areas == area_label
        area_indices = set(np.argwhere(area))
        for space_idx in area_indices:
            # argwhere returns the indices from top to bottom and left to right
            # we check for the square on the left and bottom of the space
            # so we can skip the last row and column to avoid index errors
            if space_idx[0] == field.shape[0] - 2 or space_idx[1] == field.shape[1] - 2:
                continue

            needed_indices = set(
                [
                    tuple(space_idx),
                    tuple(space_idx + np.array([0, 1])),
                    tuple(space_idx + np.array([1, 0])),
                    tuple(space_idx + np.array([1, 1])),
                ]
            )

            if needed_indices <= set([tuple(idx) for idx in area_indices]):
                score += 6
                break

    return score


def traykloster(field):
    connected_areas = ski.measure.label(
        field == SpaceType.HOUSE.value, background=False, connectivity=1
    )

    score = 0
    for area_label in np.unique(connected_areas):
        if area_label == 0:
            continue

        area = connected_areas == area_label
        for line in area.tolist() + area.T.tolist():
            house_counts = [
                sum(1 for _ in group) for val, group in groupby(line) if val
            ]
            n_houses = max(house_counts) if len(house_counts) > 0 else 0
            if n_houses >= 4:
                score += 7
                break

    return score


HOUSE_SCORING_CARDS = [
    ScoringCard(
        "Bastionen in der Wildnis",
        134,
        TaskType.HOUSE,
        bastionen_der_wildnis,
        16,
        "8 Punkte für jedes Dorf-Gebite das aus minedstens 6 Dorf-Feldern besteht.",
    ),
    ScoringCard(
        "Metropole",
        135,
        TaskType.HOUSE,
        metropole,
        16,
        "1 Ruhmpunkt für jedes Dorf-Feld in deinem größten Dorf-Gebiet, das nicht an ein oder mehrere Gebirgs-Felder angrenzt.",
    ),
    ScoringCard(
        "Schild des Reiches",
        137,
        TaskType.HOUSE,
        schild_des_reiches,
        20,
        "2 Ruhmpunkte für jedes Dorf-Feld in deinem zweitgrößten Dorf-Gebiet.",
    ),
    ScoringCard(
        "Schillernde Ebene",
        136,
        TaskType.HOUSE,
        schillernde_ebene,
        21,
        "3 Ruhmpunkte für jedes Dorf-Gebiet das an mindestens 3 unterschieldiche Geländearten angrenzt.",
    ),
    ScoringCard(
        "Karawanserei",
        239,
        TaskType.HOUSE,
        karawanserei,
        16,
        "1 Ruhmpunkt für jede Zeile und Spalte mit mindestens 1 Feld eines von dir gewählten Dorf-Gebietes.",
    ),
    ScoringCard(
        "Die äußerste Enklave",
        237,
        TaskType.HOUSE,
        die_aeusserste_enklave,
        12,
        "1 Ruhmpunkt für jedes leere Feld, das an ein von dir gewähltes Dorf-Gebiet angrenzt.",
    ),
    ScoringCard(
        "Gnomkolonie",
        238,
        TaskType.HOUSE,
        gnomkolonie,
        12,
        "6 Ruhmpunkte für jedes Dorf-Gebite mit mindestens 1 ausgefüllten Quadrat der größe 2x2.",
    ),
    ScoringCard(
        "Traykloster",
        236,
        TaskType.HOUSE,
        traykloster,
        14,
        "7 Ruhmpunkte für jedes Dorf-Gebiet mit mindestens 1 ausgefüllten Rechteck der größe 1x4 (oder 4x1).",
    ),
]
