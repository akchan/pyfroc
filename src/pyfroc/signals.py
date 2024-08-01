#!/usr/bin/env python
# coding: UTF-8

from abc import ABC, abstractmethod
from collections.abc import Sequence
from dataclasses import dataclass
from typing import TypeVar

import math

from pyfroc.coords import Coordinates

T_BaseSignal = TypeVar("T_BaseSignal", "BaseLesion", "BaseResponse")
T_Signal = TypeVar("T_Signal", "Lesion", "Response")


@dataclass(frozen=True)
class BaseLesion(ABC):
    coords: Coordinates

    @abstractmethod
    def __eq__(self, other: T_BaseSignal) -> bool:
        raise NotImplementedError("This method should be implemented in subclasses.")

    @abstractmethod
    def distance(self, other) -> float:
        raise NotImplementedError("This method should be implemented in subclasses.")


@dataclass(frozen=True)
class BaseResponse(BaseLesion):
    confidence: float | int

    @abstractmethod
    def is_true_positive(self, lesion: "BaseLesion") -> bool:
        raise NotImplementedError("This method should be implemented in subclasses.")

    @abstractmethod
    def to_lesion(self) -> "BaseLesion":
        raise NotImplementedError("This method should be implemented in subclasses.")

    @abstractmethod
    def get_confidence(self) -> float:
        raise NotImplementedError("This method should be implemented in subclasses.")


@dataclass(frozen=True)
class Lesion(BaseLesion):
    r: float
    name: str

    def __post_init__(self):
        assert isinstance(self.coords, Coordinates), f"coords should be Coordinates or subclasses, not {type(self.coords)}"
        assert self.r > 0.0, f"r should be greater than 0, not {self.r}"

    def __eq__(self, other: "Lesion") -> bool:
        return self.coords == other.coords and math.isclose(self.r, other.r) and self.name == other.name

    def distance(self, other: T_Signal) -> float:
        return self.coords.distance(other.coords)


@dataclass(frozen=True)
class Response(BaseResponse):
    r: float
    name: str

    def __post_init__(self):
        assert self.r > 0.0, f"r should be greater than 0, not {self.r}"
        assert isinstance(self.confidence, (float, int)), f"confidence should be float, not {type(self.confidence)}"

    def __eq__(self, other: "Response") -> bool:
        return self.coords == other.coords and math.isclose(self.r, other.r) and self.name == other.name and self.confidence == other.confidence

    def distance(self, other: T_Signal) -> float:
        return self.coords.distance(other.coords)

    def get_confidence(self) -> float:
        return float(self.confidence)

    def is_true_positive(self, lesion: Lesion) -> bool:
        return self.distance(lesion) <= lesion.r

    def to_lesion(self) -> Lesion:
        return Lesion(self.coords, self.r, self.name)


def sort_signals(signals: Sequence[T_BaseSignal]) -> Sequence[T_BaseSignal]:
    """
    Sorts a list of signals based on their coordinates in ascending order.

    Args:
        signals (list[Lesion | Response]): A list of signals to be sorted.

    Returns:
        list[Lesion | Response]: A new list of signals sorted based on their coordinates.
    """
    return sorted(signals, key=lambda s: (s.coords.z, s.coords.y, s.coords.x))
