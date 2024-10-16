#!/usr/bin/env python
# coding: UTF-8

from abc import ABC, abstractmethod
from collections.abc import Sequence
from dataclasses import dataclass
import math
from typing import TypeVar


import numpy as np


from pyfroc.coords import Coordinates, ScannerCoordinates
from pyfroc.miniball_util import get_min_sphere


# Type definitions
T_BaseSignal = TypeVar("T_BaseSignal", "BaseLesion", "BaseResponse")
T_Signal = TypeVar("T_Signal", "Lesion", "Response")
T_TruePositives = Sequence[tuple["BaseLesion", "BaseResponse"]]
T_FalsePositives = Sequence["BaseResponse"]


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

    @classmethod
    def from_mask(cls, name: str,
                  confidence: float,
                  mask: np.ndarray,
                  space_directions: np.ndarray,
                  origin: np.ndarray = np.zeros(3)) -> "Response":
        """Response is approximated by a minimum sphere that encloses the mask.

        Args:
            name (str): Name of the response
            confidence (float): Conficence for postive.
            mask (np.ndarray): 3D mask of the response
            space_directions (np.ndarray): a matrix of shape (3, 3) where each row is a direction vector.
            origin (np.ndarray, optional): Coordinates of origin of the series. Defaults to np.zeros(3).

        Returns:
            Response: A new Response object.
        """
        c, r = Response.mask2minisphere(mask, space_directions, origin)
        assert r > 0.0, f"Invalid radius {r = }"

        return Response(coords=ScannerCoordinates(*c),
                        r=r,
                        name=name,
                        confidence=confidence)

    @staticmethod
    def mask2minisphere(mask: np.ndarray,
                        space_directions: np.ndarray,
                        origin: np.ndarray = np.zeros(3),
                        mask_dtype=np.int8) -> tuple[np.ndarray, float]:
        mask = (mask > 0).astype(mask_dtype)

        assert mask.max() > 0, "mask should have at least one positive cell"

        # Convert idx to scanner coordinates
        xx, yy, zz = np.where(mask > 0)
        idx = np.array([xx, yy, zz], dtype=np.float32)

        # (n_points, 3)
        edge_coords = np.dot(space_directions.T, idx).T + origin

        if len(edge_coords) == 1:
            r = np.max(space_directions)
            return edge_coords[0], r

        c, r = get_min_sphere(edge_coords)

        return c, r

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
