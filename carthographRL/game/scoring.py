from enum import Enum
from itertools import groupby
from typing import List

import numpy as np
import skimage as ski

from .terrains import Terrains


class TaskType(Enum):
    VILLAGE = 1
    WATER_FARM = 2
    FOREST = 3
    GEOMETRY = 4


# TODO make datclass
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

    def is_hero(self):
        if self.card_id % 100 == 1:
            return False
        elif self.card_id % 100 == 2:
            return True
        else:
            raise ValueError("Card ID is invalid.")

    def __repr__(self):
        return self.name


def bastionen_der_wildnis(field):
    connected_areas = ski.measure.label(
        field == Terrains.VILLAGE.value, background=False, connectivity=1
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
        field == Terrains.VILLAGE.value, background=False, connectivity=1
    )
    area_labels, area_sizes = np.unique(connected_areas, return_counts=True)

    area_sizes_sorted = np.sort(area_sizes)[::-1]
    area_lablels_sorted = area_labels[np.argsort(area_sizes)[::-1]]

    for area_label, area_size in zip(area_lablels_sorted, area_sizes_sorted):
        if area_label == 0:  #  background is labeled 0
            continue

        area = connected_areas == area_label
        surrounding_mask = ski.segmentation.find_boundaries(
            area, mode="outer", connectivity=1
        )
        if Terrains.MOUNTAIN.value not in field[np.argwhere(surrounding_mask)]:
            return area_size

    return 0


def schild_des_reiches(field):
    connected_areas = ski.measure.label(
        field == Terrains.VILLAGE.value, background=False, connectivity=1
    )
    area_labels, area_sizes = np.unique(connected_areas, return_counts=True)

    if len(area_labels) < 3:
        # there is only one or no house area so there is no second largest area
        return 0

    return np.sort(area_sizes)[-2] * 2


def schillernde_ebene(field):
    connected_areas = ski.measure.label(
        field == Terrains.VILLAGE.value, background=False, connectivity=1
    )

    score = 0
    for area_label in np.unique(connected_areas):
        if area_label == 0:  #  background is labeled 0
            continue

        surrounding_mask = ski.segmentation.find_boundaries(
            connected_areas == area_label, mode="outer", connectivity=1
        )
        surrounding_types = list(np.unique(field[np.argwhere(surrounding_mask)]))
        surrounding_types.remove(Terrains.EMPTY.value)
        if len(surrounding_types) >= 3:
            score += 3

    return score


def karawanserei(field):
    connected_areas = ski.measure.label(
        field == Terrains.VILLAGE.value, background=False, connectivity=1
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
        field == Terrains.VILLAGE.value, background=False, connectivity=1
    )

    scores = []
    for area_label in np.unique(connected_areas):
        if area_label == 0:
            continue

        surrounding_mask = ski.segmentation.find_boundaries(
            connected_areas == area_label, mode="outer", connectivity=1
        )
        surrounding_spaces = field[np.argwhere(surrounding_mask)]
        scores.append(len(surrounding_spaces == Terrains.EMPTY.value))

    if len(scores) == 0:
        return 0

    return max(scores)


def gnomkolonie(field):
    connected_areas = ski.measure.label(
        field == Terrains.VILLAGE.value, background=False, connectivity=1
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
        field == Terrains.VILLAGE.value, background=False, connectivity=1
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


def pfad_des_waldes(field):
    connected_areas = ski.measure.label(
        field == Terrains.FOREST.value, background=False, connectivity=1
    )

    bonus_mountains_indices = set()
    for area_label in np.unique(connected_areas):
        if area_label == 0:
            continue

        surrounding_mask = ski.segmentation.find_boundaries(
            connected_areas == area_label, mode="outer", connectivity=1
        )

        connected_mountains_indices = np.argwhere(
            np.logical_and(surrounding_mask, field == Terrains.MOUNTAIN.value)
        )
        if len(connected_mountains_indices) > 1:
            bonus_mountains_indices.update(
                set([tuple(idx) for idx in connected_mountains_indices])
            )

    return len(bonus_mountains_indices) * 3


def schildwald(field):
    edge = np.concatenate((field[0, :], field[-1, :], field[1:-1, 0], field[1:-1, -1]))

    return np.count_nonzero(edge == Terrains.FOREST.value)


def gruenflaeche(field):
    n_lines = 0

    for row in field:
        if Terrains.FOREST.value in row:
            n_lines += 1

    for col in field.T:
        if Terrains.FOREST.value in col:
            n_lines += 1

    return n_lines


def duesterwald(field):
    score = 0

    for forest_idx in np.argwhere(field == Terrains.FOREST.value):
        f = np.full(field.shape, 0)
        f[forest_idx[0], forest_idx[1]] = 1
        surrounding_mask = ski.segmentation.find_boundaries(
            f, mode="outer", connectivity=1
        )

        if Terrains.EMPTY.value not in field[np.argwhere(surrounding_mask)]:
            score += 1

    return score


def goldener_kornspeicher(field):
    # TODO this is the only scoring card in cartographers that uses the tempel field
    # we need to implement the handling of the tempel field first
    raise NotImplementedError()


def tal_der_magier(field):
    score = 0

    for water_idx in np.argwhere(field == Terrains.WATER.value):
        f = np.full(field.shape, 0)
        f[water_idx[0], water_idx[1]] = 1
        surrounding_mask = ski.segmentation.find_boundaries(
            f, mode="outer", connectivity=1
        )

        if Terrains.MOUNTAIN.value in field[np.argwhere(surrounding_mask)]:
            score += 2

    for field_idx in np.argwhere(field == Terrains.FARM.value):
        f = np.full(field.shape, 0)
        f[field_idx[0], field_idx[1]] = 1
        surrounding_mask = ski.segmentation.find_boundaries(
            f, mode="outer", connectivity=1
        )

        if Terrains.MOUNTAIN.value in field[np.argwhere(surrounding_mask)]:
            score += 1

    return score


def bewaesserungskanal(field):
    score = 0

    for water_idx in np.argwhere(field == Terrains.WATER.value):
        f = np.full(field.shape, 0)
        f[water_idx[0], water_idx[1]] = 1
        surrounding_mask = ski.segmentation.find_boundaries(
            f, mode="outer", connectivity=1
        )

        if Terrains.FARM.value in field[np.argwhere(surrounding_mask)]:
            score += 1

    for field_idx in np.argwhere(field == Terrains.FARM.value):
        f = np.full(field.shape, 0)
        f[field_idx[0], field_idx[1]] = 1
        surrounding_mask = ski.segmentation.find_boundaries(
            f, mode="outer", connectivity=1
        )

        if Terrains.WATER.value in field[np.argwhere(surrounding_mask)]:
            score += 1

    return score


def ausgedehnte_straende(field):
    score = 0
    for space_type_1, space_type_2 in [
        (Terrains.FARM.value, Terrains.WATER.value),
        (Terrains.WATER.value, Terrains.FARM.value),
    ]:
        areas = ski.measure.label(
            field == space_type_1, background=False, connectivity=1
        )
        for area_label in np.unique(areas):
            if area_label == 0:
                continue

            area = areas == area_label
            area_indices = np.argwhere(area)
            surrounding_mask = ski.segmentation.find_boundaries(
                area, mode="outer", connectivity=1
            )
            surrounding_indices = np.argwhere(surrounding_mask)

            if space_type_2 not in field[surrounding_indices] and np.all(
                area_indices[:, 0] > 0
                and area_indices[:, 0] < field.shape[0] - 1
                and area_indices[:, 1] > 0
                and area_indices[:, 1] < field.shape[1] - 1
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


class ScoringDeck:
    def __init__(
        self,
        heroes: bool = False,
        rng: np.random.Generator = None,
        predefined_cards: List[ScoringCard] = None,
    ):
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

        tasks = [self.rng.choice(self._cards_by_type[t]) for t in order]

        return tasks


# class Season:
#     # @classmethod
#     # def generate_spring(cls):
#     #     return cls(
#     #         name="Frühling",

#     def __init__(self, name, time, tasks):
#         self.name = name
#         self.time = time
#         assert len(tasks) == 2
#         self.tasks = tasks

#         self.score = 0

#     def evaluate(self, map):
#         for task in self.tasks:
#             self.score += task.evaluate(board)
#         map.surrounded_mountains = 0
