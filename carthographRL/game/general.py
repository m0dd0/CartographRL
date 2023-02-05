from enum import Enum


class Corner(Enum):
    TOP_LEFT = 1
    TOP_RIGHT = 2
    BOTTOM_LEFT = 3
    BOTTOM_RIGHT = 4


class MonsterRotation(Enum):
    CLOCKWISE = 1
    COUNTER_CLOCKWISE = 2
