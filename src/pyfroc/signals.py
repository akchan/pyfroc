#!/usr/bin/env python
# coding: UTF-8

from dataclasses import dataclass
from typing import TypeVar

import math

from pyfroc.coords import Coordinates

T_Signal = TypeVar("T_Signal", "Lesion", "Response")
T_TruePositives = list[tuple["Response", "Lesion"]]
T_FalsePositives = list["Response"]


@dataclass(frozen=True)
class Lesion:
    coords: Coordinates
    r: float
    name: str

    def __post_init__(self):
        assert isinstance(self.coords, Coordinates), f"coords should be Coordinates or subclasses, not {type(self.coords)}"
        assert self.r > 0.0, f"r should be greater than 0, not {self.r}"

    def __eq__(self, other: T_Signal) -> bool:
        return self.coords == other.coords and math.isclose(self.r, other.r) and self.name == other.name

    def distance(self, other: T_Signal) -> float:
        return self.coords.distance(other.coords)


@dataclass(frozen=True)
class Response(Lesion):
    confidence: float | int

    def __post_init__(self):
        super().__post_init__()
        assert isinstance(self.confidence, (float, int)), f"confidence should be float, not {type(self.confidence)}"

    def is_true_positive(self, lesion: Lesion) -> bool:
        return self.distance(lesion) <= lesion.r

    def to_lesion(self) -> Lesion:
        return Lesion(self.coords, self.r, self.name)


def sort_signals(signals: list[T_Signal]) -> list[T_Signal]:
    """
    Sorts a list of signals based on their coordinates in ascending order.

    Args:
        signals (list[Lesion | Response]): A list of signals to be sorted.

    Returns:
        list[Lesion | Response]: A new list of signals sorted based on their coordinates.
    """
    return sorted(signals, key=lambda s: (s.coords.z, s.coords.y, s.coords.x))
