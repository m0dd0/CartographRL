from enum import Enum
from typing import List, Callable
from dataclasses import dataclass

import numpy as np

from .general import Terrains, Card
from .map import Map, Cluster


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


def bastionen_der_wildnis(map_sheet: Map) -> int:
    """8 Punkte für jedes Dorf-Gebite das aus minedstens 6 Dorf-Feldern besteht."""
    clusters = map_sheet.clusters(Terrains.VILLAGE)
    return len([c for c in clusters if len(c) >= 6]) * 8


def metropole(map_sheet: Map) -> int:
    """1 Ruhmpunkt für jedes Dorf-Feld in deinem größten Dorf-Gebiet, das nicht an ein oder mehrere Gebirgs-Felder angrenzt."""
    clusters = map_sheet.clusters(Terrains.VILLAGE)

    valid_cluster_sizes = []
    for c in clusters:
        if Terrains.VILLAGE.value not in c.surrounding_terrains():
            valid_cluster_sizes.append(len(c))

    return max(valid_cluster_sizes) if valid_cluster_sizes else 0


def schild_des_reiches(map_sheet: Map) -> int:
    """2 Ruhmpunkte für jedes Dorf-Feld in deinem zweitgrößten Dorf-Gebiet."""
    clusters = map_sheet.clusters(Terrains.VILLAGE)
    if len(clusters) < 3:
        return 0

    return sorted(len(c) for c in clusters)[-2] * 2


def schillernde_ebene(map_sheet: Map) -> int:
    """3 Ruhmpunkte für jedes Dorf-Gebiet das an mindestens 3 unterschieldiche Geländearten angrenzt."""

    clusters = map_sheet.clusters(Terrains.VILLAGE)

    score = 0
    for c in clusters:
        surrounding_terrain_types = set(c.surrounding_terrains())
        surrounding_terrain_types.remove(Terrains.EMPTY.value)
        # TODO are there any other terrains that should be removed? monsters, wasteland, etc?
        if len(set(c.surrounding_terrains())) >= 3:
            score += 3

    return score


def karawanserei(map_sheet: Map) -> int:
    """1 Ruhmpunkt für jede Zeile und Spalte mit mindestens 1 Feld eines von dir gewählten Dorf-Gebietes."""

    clusters = map_sheet.clusters(Terrains.VILLAGE)

    scores = []
    for c in clusters:
        n_rows = np.max(c.coords[:, 0]) - np.min(c.coords[:, 0]) + 1
        n_cols = np.max(c.coords[:, 1]) - np.min(c.coords[:, 1]) + 1

        scores.append(n_rows + n_cols)

    return max(scores) if scores else 0


def die_aeusserste_enklave(map_sheet: Map) -> int:
    """1 Ruhmpunkt für jedes leere Feld, das an ein von dir gewähltes Dorf-Gebiet angrenzt."""

    clusters = map_sheet.clusters(Terrains.EMPTY)

    scores = []
    for c in clusters:
        scores.append(len(c.surrounding_values() == Terrains.VILLAGE.value))

    return max(scores) if scores else 0


def gnomkolonie(map_sheet: Map) -> int:
    """6 Ruhmpunkte für jedes Dorf-Gebite mit mindestens 1 ausgefüllten Quadrat der größe 2x2."""

    clusters = map_sheet.clusters(Terrains.VILLAGE)

    shape = np.array([[0, 0], [0, 1], [1, 0], [1, 1]])

    score = 0
    for c in clusters:
        cluster_coords_set = set([tuple(idx) for idx in c.coords])
        for pivot_coord in c.coords:
            needed_coords = set([tuple(pivot_coord + s) for s in shape])

            if needed_coords <= cluster_coords_set:
                score += 6
                break

    return score


def traykloster(map_sheet: Map) -> int:
    """7 Ruhmpunkte für jedes Dorf-Gebiet mit mindestens 1 ausgefüllten Rechteck der größe 1x4 (oder 4x1)."""

    clusters = map_sheet.clusters(Terrains.VILLAGE)

    shape_1 = np.array([[0, 0], [0, 1], [0, 2], [0, 3]])
    shape_2 = np.array([[0, 0], [1, 0], [2, 0], [3, 0]])

    score = 0
    for c in clusters:
        cluster_coords_set = set([tuple(idx) for idx in c.coords])
        for pivot_coord in c.coords:
            if (
                set([tuple(pivot_coord + s) for s in shape_1]) <= cluster_coords_set
                or set([tuple(pivot_coord + s) for s in shape_2]) <= cluster_coords_set
            ):
                score += 7
                break

    return score


def pfad_des_waldes(map_sheet: Map) -> int:
    """3 Ruhmpunkte für jedes Gebirgs-Feld, das über mindestens 1 Wald-Gebiet mit mindestens 1 anderen Gebirgs-Feld verbunden ist."""

    clusters = map_sheet.clusters(Terrains.FOREST)

    connected_mountains = set()
    for c in clusters:
        mountain_coords = np.argwhere(c.surrounding_map() == Terrains.MOUNTAIN.value)
        if len(mountain_coords) >= 2:
            connected_mountains.update(set([tuple(c) for c in mountain_coords]))

    return len(connected_mountains) * 3


def schildwald(map_sheet: Map) -> int:
    """1 Ruhmpunkt für jedes Wald-Feld das an den Rand grenzt."""

    edge = np.concatenate(
        (map_sheet[0, :], map_sheet[-1, :], map_sheet[1:-1, 0], map_sheet[1:-1, -1])
    )

    return np.count_nonzero(edge == Terrains.FOREST.value)


def gruenflaeche(map_sheet: Map) -> int:
    """1 Ruhmpunkt für jede Zeile und Spalte mit mindestens 1 Wald-Feld."""

    n_lines = 0

    for line in np.concatenate((map_sheet.terrain_map, map_sheet.terrain_map.T)):
        if Terrains.FOREST.value in line:
            n_lines += 1

    return n_lines


def duesterwald(map_sheet: Map) -> int:
    """1 Ruhmpunkt für jedes Wald-Feld das an 4 ausgefüllte Felder (und/oder den Rand) angrenzt."""

    score = 0
    for c in np.argwhere(map_sheet.terrain_map == Terrains.FOREST.value):
        if map_sheet.is_surrounded(c):
            score += 1

    return score


def goldener_kornspeicher(map_sheet: Map) -> int:
    """1 Ruhmpunkt für jedes Wasser-Feld, das an minestens 1 Ruinen-Feld grenzt. 3 Ruhmpunkte für jedes Acker-Feld, auf einem Ruinen-Feld."""

    score = 0
    for water_coord in np.argwhere(map_sheet.terrain_map == Terrains.WATER.value):
        c = Cluster([water_coord], map_sheet)
        if any(surr in map_sheet.ruin_coords for surr in c.surrounding_coords()):
            score += 1

    for field_coord in np.argwhere(map_sheet.terrain_map == Terrains.FIELD.value):
        if field_coord in map_sheet.ruin_coords:
            score += 3

    return score


def tal_der_magier(map_sheet: Map) -> int:
    """2 Ruhmpunkte für jedes Wasser-Feld, das an mindestens 1 Gebirgs-Feld grenzt. 1 Ruhmpunkt für jedes Acker-Feld, das an mindestens 1 Gebirgs-Feld grenzt."""

    mountain_coords = np.argwhere(map_sheet.terrain_map == Terrains.MOUNTAIN.value)

    score = 0
    for water_coord in np.argwhere(map_sheet.terrain_map == Terrains.WATER.value):
        c = Cluster([water_coord], map_sheet)
        if any(surr in mountain_coords for surr in c.surrounding_coords()):
            score += 2

    for field_coord in np.argwhere(map_sheet.terrain_map == Terrains.FIELD.value):
        c = Cluster([field_coord], map_sheet)
        if any(surr in mountain_coords for surr in c.surrounding_coords()):
            score += 1

    return score


def bewaesserungskanal(map_sheet: Map) -> int:
    """1 Ruhmpunkt für jedes Wasser-Feld, das an mindestens 1 Acker-Feld grenzt. 1 Ruhmpunkt für jedes Acker-Feld, das an mindestens 1 Wasser-Feld grenzt."""

    water_coords = np.argwhere(map_sheet.terrain_map == Terrains.WATER.value)
    field_coords = np.argwhere(map_sheet.terrain_map == Terrains.FIELD.value)

    score = 0
    for water_coord in water_coords:
        c = Cluster([water_coord], map_sheet)
        if any(surr in field_coords for surr in c.surrounding_coords()):
            score += 1

    for field_coord in field_coords:
        c = Cluster([field_coord], map_sheet)
        if any(surr in water_coords for surr in c.surrounding_coords()):
            score += 1

    return score


def ausgedehnte_straende(map_sheet: Map) -> int:
    """3 Ruhmpunkte für für jedes Acker-Gebiet, das weder an den Rand noch an 1 oder mehrere Wasser-Felder grenzt. 3 Ruhmpunkte für jedes Wasser-Gebiet, das weder an den Rand noch an 1 oder mehrere Acker-Felder grenzt."""
    score = 0
    for c in map_sheet.clusters(Terrains.FIELD):
        if Terrains.WATER.value not in c.surrounding_terrains() and not c.on_edge():
            score += 3

    for c in map_sheet.clusters(Terrains.WATER):
        if Terrains.FIELD.value not in c.surrounding_terrains() and not c.on_edge():
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
