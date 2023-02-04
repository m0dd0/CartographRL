from abc import ABC, abstractmethod
from enum import Enum

import numpy as np

# task type enum
class TaskType(Enum):
    HOUSE = 1
    SEA_FIELD = 2
    FOREST = 3
    SIZE = 4	

class AreaType(Enum):
    HOUSE = 1
    SEA = 2
    FOREST = 3
    FIELD = 4
    DEVIL = 5
    EMPTY = 6
    MOUNTAIN = 7
    WASTE = 8

class ScoringCard:
    def __init__(self, name, card_id, task_type, evaluation_function, description=None):
        self.name = name
        self.card_id = card_id
        self.type = type
        self.evaluation_function = evaluation_function

    def evaluate(self, field):
        return self.evaluation_function(field)

    def __repr__(self):
        return self.name

class Field:
    # TODO try numpy array based implementation
    def __init__(self, n_rows:int=11, n_cols:int=11):
        self.n_rows = n_rows
        self.n_cols = n_cols
        self._field = np.full((n_rows, n_cols), AreaType.EMPTY.value, dtype=np.int8)

    def connected_areas(self, area_type:AreaType):
        self._field

def get_areas(field):
    pass

def bastionen_der_wildnis(field):
    pass

# Karthograph: 41 cards
# Karthographin: 43 cards
HOUSE_SCORING_CARDS = [
    ScoringCard("Bastionen in der Wildnis", 134, TaskType.HOUSE, )