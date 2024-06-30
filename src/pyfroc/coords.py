#!/usr/bin/env python
# coding: UTF-8


from dataclasses import dataclass

import numpy as np


@dataclass(frozen=True)
class Coordinates:
    x: float
    y: float
    z: float = 0.0

    @classmethod
    def from_idx(cls, idx: tuple[int, int, int],
                 spacing_direction: np.ndarray,
                 origin: np.ndarray) -> "Coordinates":
        """Create ScannerCoordinates from indices and Series information
        Í
        Args:
            idx (tuple[int, int, int]): A tuple of indices (x, y, z)
            spacing_direction (np.ndarray): A spacing direction matrix (3, 3). Each row represents a direction vector.
            origin (np.ndarray): origin of the coordinate system

        Returns:
            ScannerCoordinates: A ScannerCoordinates object
        """
        coords = np.dot(spacing_direction.T, np.array(idx)) + origin

        return cls(coords[0], coords[1], coords[2])

    def distance(self, other: "Coordinates") -> float:
        return self._distance(other)

    def numpy(self, dtype=np.float32) -> np.ndarray:
        return np.array([self.x, self.y, self.z], dtype=dtype)

    def to_idx(self, spacing_direction: np.ndarray, origin: np.ndarray) -> tuple[int, int, int]:
        coords = np.array([self.x, self.y, self.z])

        try:
            spacing_direction_inv = np.linalg.inv(spacing_direction.T)
        except np.linalg.LinAlgError as e:
            raise np.linalg.LinAlgError(f"The spacing direction matrix is singular. spacing_direction: {spacing_direction}") from e

        idx = np.round(np.dot(spacing_direction_inv, coords - origin)).astype(np.int32)

        return (idx[0], idx[1], idx[2])

    def _add(self, other):
        return self.__class__(self.x + other.x, self.y + other.y, self.z + other.z)

    def _sub(self, other):
        return self.__class__(self.x - other.x, self.y - other.y, self.z - other.z)

    def _mul(self, other):
        return self.__class__(self.x * other.x, self.y * other.y, self.z * other.z)

    def _truediv(self, other):
        return self.__class__(self.x / other.x, self.y / other.y, self.z / other.z)

    def _distance(self, other) -> float:
        return ((self.x - other.x) ** 2 + (self.y - other.y) ** 2 + (self.z - other.z) ** 2) ** 0.5

    def __eq__(self, other: "Coordinates") -> bool:
        return np.allclose(self.numpy(), other.numpy())


class ScannerCoordinates(Coordinates):

    def __add__(self, other: "ScannerCoordinates"):
        return self._add(other)

    def __sub__(self, other: "ScannerCoordinates"):
        return self._sub(other)

    def __mul__(self, other: "ScannerCoordinates"):
        return self._mul(other)

    def __truediv__(self, other: "ScannerCoordinates"):
        return self._truediv(other)

    def distance(self, other: "ScannerCoordinates") -> float:
        return self._distance(other)


class SeriesCoordinates(Coordinates):
    def __add__(self, other: "SeriesCoordinates"):
        return self._add(other)

    def __sub__(self, other: "SeriesCoordinates"):
        return self._sub(other)

    def __mul__(self, other: "SeriesCoordinates"):
        return self._mul(other)

    def __truediv__(self, other: "SeriesCoordinates"):
        return self._truediv(other)

    def distance(self, other: "SeriesCoordinates") -> float:
        return self._distance(other)
