#!/usr/bin/env python
# coding: UTF-8


from dataclasses import dataclass

import numpy as np


@dataclass(frozen=True)
class Coordinates:
    x: float
    y: float
    z: float = 0.0

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

    def distance(self, other: "Coordinates") -> float:
        return self._distance(other)

    def numpy(self, dtype=np.float32) -> np.ndarray:
        return np.array([self.x, self.y, self.z], dtype=dtype)


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
