#!/usr/bin/env python
# coding: UTF-8


from typing import Union, Protocol


class Lesion:
    def __init__(self, coords: list[float, float, float],
                 radius: Union[float, int] = None):
        self.coords = list(coords)
        self.r = float(radius)


class Response(Lesion):
    pass


class OsirixROIReader:
    @classmethod
    def readdir(cls, dirpath):
        pass


class ResponseReferee(Protocol):
    def judge(self, responses: list[Response], lesions: list[Lesion]) -> tuple[list[Response], list[Response]]:
        tp = []
        fp = []

        return tp, fp


def main():
    pass


if __name__ == '__main__':
    main()
